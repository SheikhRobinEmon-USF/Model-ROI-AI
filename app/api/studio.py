"""Local studio API, enabled only by the desktop launcher."""
import os
from pathlib import Path
from typing import Literal
from uuid import UUID
from threading import Lock
from itertools import combinations
from app.evaluation import paired_exact
from contextlib import contextmanager

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, model_validator
from app.datasets.analytical import analytical_cases
from app.datasets.attachments import extract
from app.datasets.validate import validate_jsonl
from app.execution.local_run import run
from app.providers.local import installed_match, request
from app.storage.history import load, list_runs, save
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
        yield
    finally:
        lock.release()


class Settings(BaseModel):
    models: list[str] = Field(min_length=1,max_length=3)
    @model_validator(mode="after")
    def known_models(self):
        if len(set(self.models)) != len(self.models) or set(self.models)-MODELS.keys():
            raise ValueError("Select distinct supported models.")
        return self

class Question(Settings):
    prompt: str = Field(min_length=1,max_length=8000)
    reference: str = Field(default="",max_length=1800)
    judge: bool = True

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
        result=evaluate(body.prompt,body.models)
        if body.judge:
            grade_remaining(result,body.reference)
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
        result=compare(cases,body.models) if len(body.models)>1 else run(cases,model=body.models[0])
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
        return {"excerpt":extract(name,bytes(data))}
    except Exception as exc:
        raise HTTPException(422,f"Cannot read file: {exc}") from exc

@router.get("/history")
def history():
    return list_runs()

@router.get("/history/{run_id}")
def saved(run_id: UUID):
    try:
        return load(str(run_id))
    except FileNotFoundError:
        raise HTTPException(404,"Run no longer available.")

@router.post("/history/{run_id}/grade")
def regrade(run_id: UUID):
    with exclusive():
        result=saved(run_id)
        if result.get("evidence_type")!="custom_prompt":
            raise HTTPException(422,"Only prompt runs support rubric grading.")
        grade_remaining(result,result.get("judge_reference",""))
        save(result)
        return result
