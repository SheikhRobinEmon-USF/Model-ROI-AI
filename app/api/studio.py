"""Local studio API, enabled only by the desktop launcher."""
import os
import json
from queue import Queue
from threading import Thread
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool
from app.execution.performance import current, run_scope, emit, rate_once
from pathlib import Path
from typing import Literal
from uuid import UUID
from threading import Lock
from itertools import combinations
from app.evaluation import paired_exact
from contextlib import contextmanager

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, model_validator
from app.graders.quality import rating, comparison_summary
from app.datasets.analytical import analytical_cases
from app.datasets.attachments import extract
from app.datasets.validate import validate_jsonl
from app.execution.local_run import run
from app.providers.local import installed_match, request
from app.storage.history import delete_chat, load, list_runs, save
from app.ui.comparison import MODELS, compare, mix_workloads
from app.ui.prompt_compare import evaluate, grade_remaining


def private(req: Request):
    host = req.headers.get("host","")
    if os.environ.get("MODELROI_ENABLE_LOCAL","").lower() != "true" or host.split(":")[0] not in {"localhost","127.0.0.1"}:
        raise HTTPException(403,"Start the local launcher to use the studio.")
    if req.method == "POST" and req.headers.get("origin") != f"http://{host}":
        raise HTTPException(403,"Use the local studio tab.")

router = APIRouter(prefix="/studio", dependencies=[Depends(private)])
lock = Lock()

@contextmanager
def exclusive():
    if not lock.acquire(False):
        raise HTTPException(409,"Another evaluation is running.")
    try:
        if current.get() is None:
            with run_scope():
                yield
        else:
            yield
    finally:
        lock.release()


class Settings(BaseModel):
    models: list[str] = Field(min_length=1,max_length=2)
    @model_validator(mode="after")
    def known_models(self):
        if len(set(self.models)) != len(self.models) or set(self.models)-MODELS.keys():
            raise ValueError("Select distinct supported models.")
        return self

class Question(Settings):
    parent_id: UUID | None = None
    prompt: str = Field(min_length=1,max_length=8000)

class Benchmark(Settings):
    suite: Literal["analytical","standard"]
    count: int = Field(ge=1,le=50)
    category: str = "all"

@router.get("/models")
def models():
    try:
        tags = request("/api/tags").get("models",[])
    except OSError as exc:
        raise HTTPException(503,"Open Ollama and refresh model status.") from exc
    return [{"id":tag,"name":name,"installed":bool(installed_match(tag,tags))} for tag,name in MODELS.items()]

@router.post("/prompt")
def prompt(body: Question):
    with exclusive():
        previous = []
        parent = body.parent_id
        while parent and len(previous) < 6:
            turn = saved(parent)
            if turn.get("evidence_type") != "custom_prompt":
                raise HTTPException(422, "Choose a previous chat turn.")
            previous.append(turn)
            parent = turn.get("parent_id")
        result = (evaluate(body.prompt, body.models, previous) if previous
                  else evaluate(body.prompt, body.models))
        if body.parent_id:
            result["parent_id"] = str(body.parent_id)
        grade_remaining(result)
        save(result)
        return result

@router.post("/benchmark")
def benchmark(body: Benchmark):
    with exclusive():
        cases=analytical_cases() if body.suite=="analytical" else validate_jsonl((Path(__file__).resolve().parents[2]/"datasets/v1/draft_cases.jsonl").read_bytes())
        if body.category != "all":
            cases=[case for case in cases if case.task_type == body.category]
        if not cases:
            raise HTTPException(422,"No cases match that category.")
        cases=mix_workloads(cases)[:body.count]
        if len(body.models)>1:
            result=compare(cases,body.models,progress=lambda fraction,model:emit("status",message=f"Evaluating {model} · {fraction:.0%} of generations complete"))
        else:
            result=run(cases,model=body.models[0],progress=lambda done,total:emit("status",message=f"Evaluated {done} of {total} cases"))
        emit("status",message="Scoring benchmark answers with gpt-oss-20b")
        for model_run in result.get("runs", [result]):
            scores = []
            for row in model_run["results"]:
                if not row.get("output", "").strip():
                    continue
                try:
                    task = row["input"]
                    if row.get("done_reason") == "length":
                        task += "\nEvaluator note: the delivered answer was truncated."
                    row["judge"] = rate_once(rating, task, row["output"])
                    scores.append(row["judge"]["score"])
                except (ValueError, OSError, KeyError) as exc:
                    row["judge_error"] = str(exc)
            model_run["judge_mean"] = sum(scores) / len(scores) if scores else None
            model_run["judge_count"] = len(scores)
        if "runs" in result:
            pairs=[]
            for first, second in combinations(result["runs"],2):
                matched=zip(first["results"],second["results"],strict=True)
                counts=[(a["passed"],b["passed"]) for a,b in matched]
                left=counts.count((True,False))
                right=counts.count((False,True))
                pairs.append({"first":first["model_id"],"second":second["model_id"],
                              "first_only":left,"second_only":right,"p":paired_exact(left,right)})
            adjusted=0
            for i,pair in enumerate(sorted(pairs,key=lambda pair:pair["p"])):
                adjusted=max(adjusted,min(1,(len(pairs)-i)*pair["p"]))
                pair["holm_p"]=adjusted
            result["pairs"]=pairs
        save(result)
        return result

@router.post("/extract")
async def attachment(req: Request, name: str):
    data=bytearray()
    async for part in req.stream():
        if len(data)+len(part)>5_000_000:
            raise HTTPException(413,"Choose a file under 5 MB.")
        data.extend(part)
    try:
        return {"excerpt":await run_in_threadpool(extract, name, bytes(data))}
    except Exception as exc:
        raise HTTPException(422,f"Cannot read file: {exc}") from exc

class ChatEdit(BaseModel):
    action: Literal["rename", "pin", "unpin", "delete"]
    title: str = Field(default="", max_length=100)


@router.post("/chats/{run_id}")
def edit_chat(run_id: UUID, body: ChatEdit):
    with exclusive():
        report = saved(run_id)
        if report.get("evidence_type") != "custom_prompt":
            raise HTTPException(422, "Choose a chat.")
        records = list_runs()
        if any(row.get("parent_id") == str(run_id) for row in records):
            raise HTTPException(409, "This chat has newer turns. Refresh and select its latest turn.")
        if body.action == "delete":
            return {"removed": delete_chat(str(run_id), records)}
        if body.action == "rename":
            title = body.title.strip()
            if not title:
                raise HTTPException(422, "Enter a chat name.")
            report["chat_name"] = title
        else:
            report["pinned"] = body.action == "pin"
        save(report)
        return {"removed": []}


@router.get("/history")
def history():
    return list_runs()

@router.get("/history/{run_id}")
def saved(run_id: UUID):
    try:
        return load(str(run_id))
    except FileNotFoundError:
        raise HTTPException(404,"Run no longer available.")

@router.post("/history/{run_id}/summary")
def summarize(run_id: UUID):
    with exclusive():
        report = saved(run_id)
        if "comparison_summary" not in report:
            try:
                report["comparison_summary"] = comparison_summary(report)
            except (OSError, ValueError) as exc:
                raise HTTPException(503, f"Could not summarize this run: {exc}") from exc
            save(report)
        return report["comparison_summary"]


@router.post("/history/{run_id}/grade")
def regrade(run_id: UUID):
    with exclusive():
        result=saved(run_id)
        if result.get("evidence_type")!="custom_prompt":
            raise HTTPException(422,"Only prompt runs support rubric grading.")
        grade_remaining(result)
        result.pop("comparison_summary", None)
        save(result)
        return result

def stream_run(operation, body):
    events = Queue()

    def work():
        try:
            with run_scope(events.put):
                result = operation(body)
            events.put({"event":"complete", "report":result})
        except Exception as exc:
            events.put({"event":"error", "message":str(getattr(exc, "detail", exc))})
        finally:
            events.put(None)

    def lines():
        Thread(target=work, daemon=True).start()
        while (event := events.get()) is not None:
            yield json.dumps(event, allow_nan=False) + "\n"

    return StreamingResponse(lines(), media_type="application/x-ndjson",
                             headers={"Cache-Control":"no-store"})

@router.post("/live/prompt")
def live_prompt(body: Question):
    return stream_run(prompt, body)

@router.post("/live/benchmark")
def live_benchmark(body: Benchmark):
    return stream_run(benchmark, body)
