import hashlib
import json
from unittest.mock import patch
from urllib.error import HTTPError, URLError
import io

from fastapi.testclient import TestClient

from modelroi.api.main import app
from modelroi.providers.local import generate

GGUF = b"GGUF" + bytes(range(64))
DIGEST = "sha256:" + hashlib.sha256(GGUF).hexdigest()


def studio(tmp_path, monkeypatch):
    monkeypatch.setenv("MODELROI_HISTORY_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("MODELROI_ENABLE_LOCAL", "true")
    return TestClient(app, base_url="http://127.0.0.1", headers={"origin": "http://127.0.0.1"})


def refused(detail):
    return HTTPError("http://127.0.0.1:11434", 400, "Bad Request", {}, io.BytesIO(json.dumps({"error": detail}).encode()))


def test_upload_verifies_stages_and_hands_file_to_ollama(tmp_path, monkeypatch):
    client = studio(tmp_path, monkeypatch)
    seen = {}
    def push(digest, path, size):
        seen.update(digest=digest, size=size, content=path.read_bytes())
    with patch("modelroi.api.studio.push_blob", side_effect=push):
        reply = client.post("/studio/models/upload?name=../My%20Model.gguf", content=GGUF)
    assert reply.json() == {"digest": DIGEST, "size": len(GGUF), "file": "My Model.gguf"}
    assert seen == {"digest": DIGEST, "size": len(GGUF), "content": GGUF}
    assert not list((tmp_path / "uploads").iterdir())


def test_upload_rejects_files_that_are_not_gguf(tmp_path, monkeypatch):
    client = studio(tmp_path, monkeypatch)
    with patch("modelroi.api.studio.push_blob") as push:
        assert client.post("/studio/models/upload?name=weights.safetensors", content=GGUF).status_code == 422
        assert client.post("/studio/models/upload?name=model.gguf", content=b"PK\x03\x04 not a model").status_code == 422
        assert client.post("/studio/models/upload?name=model.gguf", content=b"GG").status_code == 422
    push.assert_not_called()
    assert not list((tmp_path / "uploads").iterdir())


def test_upload_reports_ollama_rejection_and_cleans_up(tmp_path, monkeypatch):
    client = studio(tmp_path, monkeypatch)
    with patch("modelroi.api.studio.push_blob", side_effect=refused("digest mismatch")):
        reply = client.post("/studio/models/upload?name=model.gguf", content=GGUF)
    assert reply.status_code == 422 and "digest mismatch" in reply.json()["detail"]
    with patch("modelroi.api.studio.push_blob", side_effect=URLError("refused")):
        assert client.post("/studio/models/upload?name=model.gguf", content=GGUF).status_code == 503
    assert not list((tmp_path / "uploads").iterdir())


def test_import_registers_uploaded_file_under_the_studio_namespace(tmp_path, monkeypatch):
    client = studio(tmp_path, monkeypatch)
    tags, created = [], []
    def ollama(path, body=None, timeout=180):
        if path == "/api/tags":
            return {"models": tags}
        created.append(body)
        tags.append({"name": body["model"], "size": 68, "details": {"family": "llama", "parameter_size": "4M", "quantization_level": "Q4_K_M"}})
        return {"status": "success"}
    form = {"name": "tuned-v1", "digest": DIGEST, "file": "model.gguf", "instructions": " Be brief. "}
    with patch("modelroi.api.studio.request", side_effect=ollama):
        assert client.post("/studio/models/import", json=form).json() == {"id": "ollama/modelroi/tuned-v1:latest", "name": "modelroi/tuned-v1:latest"}
        assert client.post("/studio/models/import", json=form).status_code == 409
        assert client.post("/studio/models/import", json={**form, "name": "Bad Name"}).status_code == 422
        assert client.post("/studio/models/import", json={**form, "name": "x", "file": "../x.gguf"}).status_code == 422
        listed = next(m for m in client.get("/studio/models").json() if m.get("custom"))
    assert created == [{"model": "modelroi/tuned-v1:latest", "files": {"model.gguf": DIGEST}, "system": "Be brief.", "stream": False}]
    assert listed["label"] == "tuned-v1" and listed["quantization"] == "Q4_K_M" and listed["created_here"]


def test_import_and_deploy_surface_ollama_explanations(tmp_path, monkeypatch):
    client = studio(tmp_path, monkeypatch)
    def ollama(path, body=None, timeout=180):
        if path == "/api/tags":
            return {"models": [{"name": "qwen3:4b"}]}
        raise refused("invalid file magic")
    with patch("modelroi.api.studio.request", side_effect=ollama):
        reply = client.post("/studio/models/import", json={"name": "tuned", "digest": DIGEST, "file": "model.gguf"})
        assert reply.status_code == 422 and reply.json()["detail"] == "Ollama could not do that: invalid file magic"
        reply = client.post("/studio/models/deploy", json={"name": "tuned", "base": "qwen3:4b", "instructions": "Hi"})
        assert reply.status_code == 422 and "invalid file magic" in reply.json()["detail"]
    with patch("modelroi.api.studio.request", side_effect=URLError("refused")):
        reply = client.post("/studio/models/deploy", json={"name": "tuned", "base": "qwen3:4b", "instructions": "Hi"})
        assert reply.status_code == 503 and "Open the Ollama app" in reply.json()["detail"]


def events(reply):
    return [json.loads(line) for line in reply.text.splitlines()]


def test_pull_relays_progress_and_returns_the_installed_model(tmp_path, monkeypatch):
    client = studio(tmp_path, monkeypatch)
    updates = [{"status": "pulling manifest"}, {"status": "pulling abc", "total": 10, "completed": 4}, {"status": "success"}]
    with patch("modelroi.api.studio.stream", return_value=iter(updates)) as pull, patch(
            "modelroi.api.studio.request", return_value={"models": [{"name": "hf.co/me/tuned-GGUF:Q4_K_M"}]}):
        out = events(client.post("/studio/live/models/pull", json={"model": " https://huggingface.co/me/tuned-GGUF:Q4_K_M "}))
    assert pull.call_args.args == ("/api/pull", {"model": "hf.co/me/tuned-GGUF:Q4_K_M", "stream": True})
    assert out[1] == {"event": "progress", "status": "pulling abc", "completed": 4, "total": 10}
    assert out[-1] == {"event": "complete", "model": {"id": "ollama/hf.co/me/tuned-GGUF:Q4_K_M", "name": "hf.co/me/tuned-GGUF:Q4_K_M"}}


def test_pull_reports_failures_and_rejects_unsafe_references(tmp_path, monkeypatch):
    client = studio(tmp_path, monkeypatch)
    with patch("modelroi.api.studio.stream", return_value=iter([{"error": "pull model manifest: file does not exist"}])):
        out = events(client.post("/studio/live/models/pull", json={"model": "nope:1b"}))
    assert out[-1]["event"] == "error" and "file does not exist" in out[-1]["message"]
    with patch("modelroi.api.studio.stream", side_effect=URLError("refused")):
        assert "Open the Ollama app" in events(client.post("/studio/live/models/pull", json={"model": "qwen3:4b"}))[-1]["message"]
        # The lock was released by the failed download.
        assert "Open the Ollama app" in events(client.post("/studio/live/models/pull", json={"model": "qwen3:4b"}))[-1]["message"]
    for bad in ("two words", "model; rm -rf /", "gpt-oss:120b-cloud", ""):
        assert client.post("/studio/live/models/pull", json={"model": bad}).status_code == 422


def test_remove_deletes_only_user_models(tmp_path, monkeypatch):
    client = studio(tmp_path, monkeypatch)
    tags = {"models": [{"name": "qwen3:4b"}, {"name": "gpt-oss:20b"}, {"name": "modelroi/tuned:latest"}]}
    with patch("modelroi.api.studio.request", return_value=tags), patch("modelroi.api.studio.delete") as delete:
        assert client.post("/studio/models/remove", json={"id": "qwen3:4b"}).status_code == 422
        assert client.post("/studio/models/remove", json={"id": "ollama/gpt-oss:20b"}).status_code == 422
        assert client.post("/studio/models/remove", json={"id": "ollama/missing:latest"}).status_code == 404
        delete.assert_not_called()
        assert client.post("/studio/models/remove", json={"id": "ollama/modelroi/tuned:latest"}).json() == {"removed": "ollama/modelroi/tuned:latest"}
    delete.assert_called_once_with("modelroi/tuned:latest")


def chat(capabilities):
    entry = {"name": "modelroi/tuned:latest"} | ({} if capabilities is None else {"capabilities": capabilities})
    with patch("modelroi.providers.local.request", side_effect=[{"models": [entry]}, {"done": True, "message": {"content": "4"}}]) as call:
        generate("ollama/modelroi/tuned:latest", "2+2?")
    return call.call_args.args[1]


def test_user_models_that_can_think_answer_without_a_reasoning_phase():
    assert chat(["completion", "thinking"])["think"] is False
    assert "think" not in chat(["completion"])
    assert "think" not in chat(None)
