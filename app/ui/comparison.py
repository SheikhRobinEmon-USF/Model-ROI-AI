"""Matched-case comparisons for local Ollama models."""
import json
from itertools import combinations, zip_longest
from collections import defaultdict
from uuid import uuid4


from app.evaluation import paired_exact, percentile
from app.execution.local_run import run
from app.providers.hosted import ROUTES
from app.providers.custom import PREFIX, tag_for

MODELS = {"qwen3:4b": "Qwen3 4B", "gemma4:e4b": "Gemma 4 E4B"}
ALL_MODELS = {**MODELS, **{model: route.label for model, route in ROUTES.items()}}
COLORS = ["#247969", "#9952a8", "#3067ac"]


def mix_workloads(cases):
    groups = defaultdict(list)
    for case in cases:
        groups[case.task_type].append(case)
    return [case for batch in zip_longest(*groups.values()) for case in batch if case is not None]


def compare(cases, models, progress=None, generate_fn=None):
    if len(set(models)) != len(models) or not 2 <= len(models) <= 5 or not cases:
        raise ValueError("Select two different models and at least one case.")
    runs = []
    for index, model in enumerate(models):
        if model not in ALL_MODELS and not model.startswith(PREFIX):
            raise ValueError("Unsupported model")
        def update(done, total):
            if progress:
                progress((index * total + done) / (len(models) * total), ALL_MODELS.get(model, tag_for(model)))
        runs.append(run(cases, model=model, progress=update, generate_fn=generate_fn))
    return {"run_id": str(uuid4()), "started_at": runs[0]["started_at"],
            "model_id": " / ".join(ALL_MODELS.get(m, tag_for(m)) for m in models),
            "evidence_type": "matched_local_comparison", "runs": runs}


def show(report):
    import altair as alt
    import pandas as pd
    import streamlit as st

    runs = report["runs"]
    summary = []
    for item in runs:
        rows = item["results"]
        times = [r["latency_ms"]/1000 for r in rows if r["status"] == "completed"]
        summary.append({"Model": MODELS.get(item["model_id"], item["model_id"]), "Passed": item["successful_cases"],
                        "Attempted": len(rows), "Success (%)": 100*item["success_rate"],
                        "Median seconds": percentile(times,.5), "Responses":len(times),
                        "Wilson low (%)":100*item["wilson_95"][0], "Wilson high (%)":100*item["wilson_95"][1]})
    frame = pd.DataFrame(summary)
    names = list(frame["Model"])
    color = alt.Color("Model:N", scale=alt.Scale(domain=list(MODELS.values()),range=COLORS),legend=None)
    st.subheader("How did the models compare?")
    st.write("Think of people taking the same quiz. The score shows who answered correctly. The clock shows how long each person typically took.")
    left,right = st.columns(2)
    for col,field,title in [(left,"Success (%)","Cases passed · higher is better"),(right,"Median seconds","Typical response time · lower is faster")]:
        col.markdown("**"+title+"**")
        base = alt.Chart(frame.dropna(subset=[field])).encode(y=alt.Y("Model:N",sort=names,title=None))
        scale = alt.Scale(domain=[0,100]) if field=="Success (%)" else alt.Scale(zero=True)
        bars = base.mark_bar(size=20,cornerRadiusEnd=4).encode(
            x=alt.X(field+":Q",scale=scale,title=field),color=color,tooltip=list(frame.columns))
        col.altair_chart(bars.properties(height=130),use_container_width=True)
    best = frame[frame.Passed==frame.Passed.max()]
    st.write(f"On these {len(runs[0]['results'])} cases, {' and '.join(best.Model)} recorded the highest pass count ({int(best.Passed.iloc[0])}).")
    valid=frame.dropna(subset=["Median seconds"])
    if len(valid)==len(frame) and (frame.Responses==frame.Attempted).all():
        fastest=valid[valid["Median seconds"]==valid["Median seconds"].min()]
        st.write(f"The shortest median response time was {fastest['Median seconds'].iloc[0]:.2f} seconds ({' and '.join(fastest.Model)}).")
    st.caption("Errors count as failed cases. Timing includes model loading when it occurs and uses completed responses only. Short runs give exploratory timing estimates.")
    st.dataframe(frame,hide_index=True)
    skills = {"math": "Math", "coding": "Coding", "case_study": "Case study"}
    breakdown = []
    for item in runs:
        for skill, label in skills.items():
            cases = [row for row in item["results"] if row["task_type"] == skill]
            if cases:
                breakdown.append({"Skill": label, "Model": MODELS.get(item["model_id"], item["model_id"]),
                                  "Passed": sum(row["passed"] for row in cases), "Cases": len(cases)})
    if breakdown:
        st.subheader("Which problems did each model solve?")
        st.dataframe(pd.DataFrame(breakdown).pivot(index="Skill", columns="Model", values="Passed"))
        st.caption("Cells count fully correct solutions in each skill. The full challenge set has two problems per skill.")

    by_model={MODELS.get(r["model_id"], r["model_id"]):{row["case_id"]:row for row in r["results"]} for r in runs}
    ids=list(by_model[names[0]])
    st.subheader("Where did answers differ?")
    matrix=pd.DataFrame([{"Case":i,**{name:("Error" if by_model[name][i]["status"]=="failed" else "Pass" if by_model[name][i]["passed"] else "Miss") for name in names}} for i in ids])
    different = matrix[names].nunique(axis=1) > 1
    st.write(f"All models had the same outcome on {int((~different).sum())} of {len(ids)} cases. Outcomes differed on {int(different.sum())}.")
    only_different = st.checkbox("Show only disagreements")
    st.dataframe(matrix[different] if only_different else matrix,hide_index=True)
    case_id=st.selectbox("Inspect the same case across models",ids)
    reference=by_model[names[0]][case_id]
    st.write(reference["input"])
    st.caption("Expected answer")
    st.json(reference["expected"])
    for col,name in zip(st.columns(len(names)),names):
        row=by_model[name][case_id]
        col.markdown("**"+name+"**")
        col.caption(row.get("error_type",row["reason"]))
        col.code(row["output"] or "(empty response)",language=None)
    with st.expander("Paired evidence and uncertainty"):
        pairs=[]
        for a,b in combinations(names,2):
            a_only=sum(by_model[a][i]["passed"] and not by_model[b][i]["passed"] for i in ids)
            b_only=sum(by_model[b][i]["passed"] and not by_model[a][i]["passed"] for i in ids)
            pairs.append({"A":a,"B":b,"A only":a_only,"B only":b_only,"Difference (pp)":100*(a_only-b_only)/len(ids),"Exact p":paired_exact(a_only,b_only)})
        adjusted=0
        for index,pair in enumerate(sorted(pairs,key=lambda p:p["Exact p"])):
            adjusted=max(adjusted,min(1,(len(pairs)-index)*pair["Exact p"]))
            pair["Holm p"]=adjusted
            pair["Evidence"]="Detected difference" if adjusted<.05 else "Insufficient evidence of a difference"
        st.dataframe(pd.DataFrame(pairs),hide_index=True)
        st.caption("The exact paired test uses cases where only one model passed. Draft labels and repeated task patterns limit generalization.")
    st.download_button("Download comparison JSON",json.dumps(report,indent=2),"model-comparison.json","application/json")
    st.download_button("Download comparison CSV",frame.to_csv(index=False),"model-summary.csv","text/csv")
