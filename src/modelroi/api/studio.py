"""Local studio API, enabled only by the desktop launcher."""
from modelroi.chat_context import chat_budget
import os
import json
from queue import Queue
from threading import Thread
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool
from modelroi.execution.performance import current, run_scope, emit, rate_once
from pathlib import Path
from typing import Literal
from uuid import UUID
from threading import Lock
from itertools import combinations
from modelroi.evaluation import paired_exact
from modelroi.evaluation_policy import Gates, rank_runs
from contextlib import contextmanager

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, model_validator
from functools import partial
from modelroi.providers import custom, hosted
from modelroi.graders.quality import rating, comparison_summary
from modelroi.datasets.analytical import analytical_cases
from modelroi.datasets.attachments import extract
from modelroi.datasets.validate import validate_jsonl
from modelroi.execution.local_run import run
from modelroi.providers.local import delete, generate, installed_match, ollama_error, push_blob, request, stream
from modelroi.storage.history import directory
import hashlib
import shutil
from modelroi.storage.history import benchmark_analytics, delete_chat, load, list_runs, save
from modelroi.ui.comparison import MODELS, compare, mix_workloads
from modelroi.ui.prompt_compare import evaluate, grade_remaining


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
    hosted_judge: bool = False
    models: list[str] = Field(min_length=1,max_length=5)
    @model_validator(mode="after")
    def known_models(self):
        ids = set(self.models)
        custom_ids = {model for model in ids if model.startswith(custom.PREFIX)}
        fixed = ids - custom_ids
        if len(ids) != len(self.models) or not (fixed <= MODELS.keys() or fixed <= hosted.ROUTES.keys()):
            raise ValueError("Select distinct supported responders.")
        if self.hosted_judge and fixed & MODELS.keys():
            raise ValueError("Choose local judging for built-in local responders.")
        if custom_ids:
            try:
                available = custom.inventory(request("/api/tags").get("models", []), MODELS)
            except OSError as exc:
                raise ValueError("Open Ollama to test a custom model.") from exc
            if not custom_ids <= {item["id"] for item in available}:
                raise ValueError("Refresh the model list and select an installed custom model.")
        return self

class Question(Settings):
    long_context: bool = False
    reference_answer: str = Field(default="", max_length=4000)
    parent_id: UUID | None = None
    prompt: str = Field(min_length=1,max_length=8000)

class Benchmark(Settings):
    gates: Gates = Field(default_factory=Gates)
    suite: Literal["analytical","standard"]
    count: int = Field(ge=1,le=50)
    category: str = "all"

@router.get("/models")
def models():
    try:
        tags = request("/api/tags").get("models",[])
    except OSError:
        tags = []
    return [{"id":tag,"name":name,"installed":bool(installed_match(tag,tags))} for tag,name in MODELS.items()] + [
        {"id": tag, "name": route.label, "provider": route.provider, "installed": hosted.configured(route),
         "judge_ready": hosted.configured(hosted.JUDGE_ROUTE)} for tag, route in hosted.ROUTES.items()] + custom.inventory(tags, MODELS)

OLLAMA_DOWN = "Ollama is not responding. Open the Ollama app, then try again."
GGUF_HELP = ("That file is not a GGUF model. Export or convert your weights to GGUF first, "
             "for example with llama.cpp's convert_hf_to_gguf.py.")


def ollama_failure(exc, fallback):
    """Prefer Ollama's own message; a refused connection means the service is not running."""
    detail = ollama_error(exc)
    if detail:
        return HTTPException(422, "Ollama could not do that: " + detail)
    return HTTPException(503, fallback if getattr(exc, "code", None) else OLLAMA_DOWN)


def installed_tags():
    try:
        return request("/api/tags").get("models", [])
    except OSError as exc:
        raise HTTPException(503, OLLAMA_DOWN) from exc


def free_name(name, installed):
    target = custom.NAMESPACE + name + ":latest"
    if installed_match(target, installed):
        raise HTTPException(409, "That model name already exists. Choose a new version name.")
    return target


class ModelDeployment(BaseModel):
    name: str = Field(pattern=custom.NAME)
    base: str = Field(min_length=1, max_length=250)
    instructions: str = Field(min_length=1, max_length=8000)


@router.post("/models/deploy")
def deploy(body: ModelDeployment):
    with exclusive():
        installed = installed_tags()
        target = free_name(body.name, installed)
        bases = set(MODELS) | {custom.tag_for(m["id"]) for m in custom.inventory(installed, MODELS)}
        if body.base not in bases or not installed_match(body.base, installed):
            raise HTTPException(422, "Select an installed local base model.")
        if not body.instructions.strip():
            raise HTTPException(422, "Enter instructions for this responder.")
        try:
            result = request("/api/create", {"model": target, "from": body.base,
                             "system": body.instructions.strip(), "stream": False}, timeout=600)
        except (OSError, ValueError) as exc:
            raise ollama_failure(exc, "Ollama could not load the base model.") from exc
        if result.get("status") != "success":
            raise HTTPException(502, "Ollama did not confirm deployment.")
        return {"id": custom.PREFIX + target, "name": target}


def upload_folder():
    """Uploads are staged beside saved runs, on disk, never in a memory-backed temp directory."""
    folder = directory().parent / "uploads"
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    for stale in folder.glob("*.part"):
        stale.unlink(missing_ok=True)
    return folder


@router.post("/models/upload")
async def upload_model(req: Request, name: str):
    """Receive a GGUF file, verify it and hand it to Ollama's blob store."""
    if not name.lower().endswith(".gguf"):
        raise HTTPException(422, GGUF_HELP)
    with exclusive():
        folder = upload_folder()
        declared = int(req.headers.get("content-length") or 0)
        # The file exists twice until Ollama has copied it into its own store.
        if declared and shutil.disk_usage(folder).free < 2 * declared:
            raise HTTPException(507, f"Not enough free disk space. Importing this model needs about {2 * declared / 1e9:.1f} GB free.")
        staged = folder / "model.part"
        digest, size = hashlib.sha256(), 0
        try:
            with staged.open("wb") as target:
                async for part in req.stream():
                    if size < 4 and not (b"GGUF"[size:size + len(part)] == part[:4 - size]):
                        raise HTTPException(422, GGUF_HELP)
                    digest.update(part)
                    target.write(part)
                    size += len(part)
            if size < 4:
                raise HTTPException(422, GGUF_HELP)
            blob = "sha256:" + digest.hexdigest()
            try:
                await run_in_threadpool(push_blob, blob, staged, size)
            except OSError as exc:
                raise ollama_failure(exc, "Ollama rejected the uploaded file.") from exc
            return {"digest": blob, "size": size, "file": Path(name).name}
        finally:
            staged.unlink(missing_ok=True)


class ModelImport(BaseModel):
    name: str = Field(pattern=custom.NAME)
    digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    file: str = Field(min_length=6, max_length=255, pattern=r"(?i)^[^/\\]+\.gguf$")
    instructions: str = Field(default="", max_length=8000)


@router.post("/models/import")
def import_model(body: ModelImport):
    """Register an uploaded GGUF file as a model the studio can compare."""
    with exclusive():
        target = free_name(body.name, installed_tags())
        payload = {"model": target, "files": {body.file: body.digest}, "stream": False}
        if body.instructions.strip():
            payload["system"] = body.instructions.strip()
        try:
            result = request("/api/create", payload, timeout=1800)
        except (OSError, ValueError) as exc:
            raise ollama_failure(exc, "Ollama could not read that model file.") from exc
        if result.get("status") != "success":
            raise HTTPException(502, "Ollama did not confirm the import.")
        return {"id": custom.PREFIX + target, "name": target}


class ModelPull(BaseModel):
    model: str = Field(min_length=1, max_length=260)

    @model_validator(mode="after")
    def pullable(self):
        self.model = self.model.strip().removeprefix("https://")
        if self.model.startswith("huggingface.co/"):
            self.model = "hf.co/" + self.model.removeprefix("huggingface.co/")
        if not custom.REFERENCE.match(self.model) or custom.is_cloud(self.model):
            raise ValueError("Enter a model name such as llama3.2:1b or hf.co/user/repo:Q4_K_M.")
        return self


@router.post("/live/models/pull")
def pull_model(body: ModelPull):
    """Download a model through Ollama, relaying its progress line by line."""
    def lines():
        def event(**fields):
            return json.dumps(fields) + "\n"
        if not lock.acquire(False):
            yield event(event="error", message="Another evaluation is running.")
            return
        try:
            for update in stream("/api/pull", {"model": body.model, "stream": True}):
                if update.get("error"):
                    yield event(event="error", message="Ollama could not download that model: " + str(update["error"]))
                    return
                yield event(event="progress", status=update.get("status", ""), completed=update.get("completed"), total=update.get("total"))
            match = installed_match(body.model, request("/api/tags").get("models", [])) or {}
            name = match.get("name") or body.model
            yield event(event="complete", model={"id": name if name in MODELS else custom.PREFIX + name, "name": name})
        except OSError as exc:
            detail = ollama_error(exc)
            yield event(event="error", message="Ollama could not download that model: " + detail if detail else OLLAMA_DOWN)
        finally:
            lock.release()
    return StreamingResponse(lines(), media_type="application/x-ndjson", headers={"Cache-Control": "no-store"})


class ModelRemoval(BaseModel):
    id: str = Field(min_length=1, max_length=300)


@router.post("/models/remove")
def remove_model(body: ModelRemoval):
    """Delete one of the user's own models from Ollama. Built-in candidates and the judge are never removable."""
    with exclusive():
        if body.id in MODELS or custom.tag_for(body.id) == custom.JUDGE:
            raise HTTPException(422, "Built-in models and the judge cannot be removed here.")
        if body.id not in {m["id"] for m in custom.inventory(installed_tags(), MODELS)}:
            raise HTTPException(404, "That model is no longer installed.")
        try:
            delete(custom.tag_for(body.id))
        except OSError as exc:
            raise ollama_failure(exc, "Ollama could not remove that model.") from exc
        return {"removed": body.id}


@router.post("/prompt")
def prompt(body: Question):
    with exclusive():
        previous = []
        parent = body.parent_id
        if body.long_context and not (body.hosted_judge or any(m in hosted.ROUTES for m in body.models)):
            raise HTTPException(422, "Long hosted context requires hosted responders.")
        max_turns = 32 if body.long_context else chat_budget().turns
        while parent and len(previous) < max_turns:
            turn = saved(parent)
            if turn.get("evidence_type") != "custom_prompt":
                raise HTTPException(422, "Choose a previous chat turn.")
            previous.append(turn)
            parent = turn.get("parent_id")
        emit("status", phase="prepare", message="Preparing the prompt and conversation context")
        if body.long_context:
            result = evaluate(body.prompt, body.models, previous, history_chars=24000)
            result["context_mode"] = "hosted_long"
        else:
            result = (evaluate(body.prompt, body.models, previous) if previous
                      else evaluate(body.prompt, body.models))
        if body.hosted_judge or any(m in hosted.ROUTES for m in body.models):
            result["judge_model"] = hosted.JUDGE
        if body.reference_answer.strip():
            result["reference_answer"] = body.reference_answer.strip()
        if body.parent_id:
            result["parent_id"] = str(body.parent_id)
        grade_remaining(result)
        emit("status", phase="save", message="Saving results to local history")
        save(result)
        return result

@router.post("/benchmark")
def benchmark(body: Benchmark):
    with exclusive():
        emit("status", phase="prepare", message="Selecting matched benchmark cases")
        cases=analytical_cases() if body.suite=="analytical" else validate_jsonl((Path(__file__).resolve().parents[3]/"datasets/v1/draft_cases.jsonl").read_bytes())
        if body.category != "all":
            cases=[case for case in cases if case.task_type == body.category]
        if not cases:
            raise HTTPException(422,"No cases match that category.")
        cases=mix_workloads(cases)[:body.count]
        emit("status", phase="generate", message="Running the first benchmark case")
        remote = body.hosted_judge or any(m in hosted.ROUTES for m in body.models)
        runner = None
        if remote:
            def runner(model, prompt):
                if model in hosted.ROUTES:
                    return hosted.generate(model, prompt)
                return generate(model, prompt)
        if len(body.models)>1:
            result=compare(cases,body.models,generate_fn=runner,progress=lambda fraction,model:emit("status",phase="generate",message=f"Evaluating {model} · {fraction:.0%} of generations complete"))
        else:
            result=run(cases,model=body.models[0],generate_fn=runner,progress=lambda done,total:emit("status",phase="generate",message=f"Evaluated {done} of {total} cases"))
        if remote:
            result["judge_model"] = hosted.JUDGE
            result["evidence_type"] = "hosted_benchmark"
        grader = partial(rating, model=hosted.JUDGE) if remote else rating
        for model_run in result.get("runs", [result]):
            if remote:
                model_run.update(evidence_type="hosted_benchmark", provider_api_cost_usd=None)
            scores = []
            for index, row in enumerate(model_run["results"], 1):
                if not row.get("output", "").strip():
                    continue
                try:
                    emit("status", phase="grade", message=f"Grading {model_run['model_id']} · case {index} of {len(model_run['results'])}")
                    task = json.dumps({"task": row["input"], "reference_answer": row["expected"]}, ensure_ascii=False)
                    if row.get("done_reason") == "length":
                        task += "\nEvaluator note: the delivered answer was truncated."
                    row["judge"] = rate_once(grader, task, row["output"])
                    scores.append(row["judge"]["score"])
                except (ValueError, OSError, KeyError) as exc:
                    row["judge_error"] = str(exc)
            model_run["judge_mean"] = sum(scores) / len(scores) if scores else None
            model_run["judge_count"] = len(scores)
            dimension_values = {}
            for row in model_run["results"]:
                for key, value in ((row.get("judge") or {}).get("dimensions") or {}).items():
                    if value is not None:
                        dimension_values.setdefault(key, []).append(value)
            model_run["quality_dimensions"] = {key: {"mean": sum(values)/len(values), "count": len(values)}
                                               for key, values in dimension_values.items()}
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
            result["ranking"]=rank_runs(result["runs"], body.gates)
        emit("status", phase="save", message="Saving results to local history")
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
            return {"removed": delete_chat(str(run_id))}
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
        emit("status", phase="save", message="Saving results to local history")
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


@router.get("/analytics/benchmarks")
def historical_benchmarks():
    return benchmark_analytics()
