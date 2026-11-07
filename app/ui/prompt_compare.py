"""Compare free-form responses without assuming a reference answer."""
from datetime import datetime, timezone
import json
from uuid import uuid4

import pandas as pd
import streamlit as st

from app.providers.local import generate, installed_match, request
from app.storage.history import save
from app.ui.comparison import MODELS


def evaluate(prompt, models):
    rows = []
    for tag in models:
        row = {"requested_model": tag}
        try:
            response = generate(tag, prompt)
            row.update(response)
            row["status"] = "Truncated" if response.get("done_reason") == "length" else "Answered"
        except (ValueError, OSError, KeyError) as exc:
            row.update(status="Error", error=str(exc))
        rows.append(row)
    return {"run_id": str(uuid4()), "started_at": datetime.now(timezone.utc).isoformat(),
            "model_id": " / ".join(MODELS[tag] for tag in models),
            "evidence_type": "custom_prompt", "prompt": prompt, "answers": rows}


def display(report):
    st.subheader("Answers to your question")
    st.write(report["prompt"])
    timings = []
    for column, row in zip(st.columns(len(report["answers"])), report["answers"]):
        name = MODELS[row["requested_model"]]
        column.markdown(f"**{name}**")
        if row["status"] == "Error":
            column.error(row["error"])
            continue
        seconds = row["latency_ms"] / 1000
        column.caption(f"{row['status']} · {seconds:.2f} s")
        column.text(row["output"])
        timings.append({"Model": name, "Seconds": seconds})
    if timings:
        st.subheader("Time to answer")
        st.bar_chart(pd.DataFrame(timings), x="Model", y="Seconds", horizontal=True)
    st.caption("Read the answers like estimates from different people. For a distance question, check which cities each chose and whether they measured driving or straight-line distance. Timing measures one attempt, including any model loading. Accuracy requires a reference answer.")
    st.download_button("Download prompt comparison", json.dumps(report, indent=2),
                       "prompt-comparison.json", "application/json")


def panel(enabled):
    prompt = st.text_area("Your question", value=st.session_state.get("last_question", ""),
                          placeholder="What is the distance from Florida to California?",
                          height=130, max_chars=8000)
    st.session_state.last_question = prompt
    models = st.multiselect("Models to compare", list(MODELS), default=list(MODELS),
                            format_func=MODELS.get)
    if enabled:
        try:
            installed = request("/api/tags").get("models", [])
        except (OSError, ValueError):
            st.error("Open Ollama on this computer, then refresh the page.")
            return
        missing = [tag for tag in models if installed_match(tag, installed) is None]
        if missing:
            st.info("To include these models, run the commands below in Terminal. You can compare the installed models now.")
            st.code("\n".join("ollama pull "+tag for tag in missing), language="bash")
    else:
        st.info("Start the local launcher to compare models on your machine.")
    if st.button("Compare answers", type="primary", disabled=not enabled or not models or not prompt.strip()):
        with st.spinner("Running the same question through each selected model…"):
            report = evaluate(prompt, models)
            save(report)
            st.session_state.result = report
    report = st.session_state.get("result", {})
    if (report.get("evidence_type") == "custom_prompt" and report["prompt"] == prompt
            and [row["requested_model"] for row in report["answers"]] == models):
        display(report)
