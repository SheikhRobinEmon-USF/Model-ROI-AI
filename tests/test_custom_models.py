from unittest.mock import patch
from fastapi.testclient import TestClient

from app.api.main import app


def test_deployment_and_comparison(tmp_path, monkeypatch):
    monkeypatch.setenv("MODELROI_HISTORY_DIR", str(tmp_path))
    monkeypatch.setenv("MODELROI_ENABLE_LOCAL", "true")
    client = TestClient(app, base_url="http://127.0.0.1", headers={"origin": "http://127.0.0.1"})
    tags = [{"name": "qwen3:4b"}]
    def ollama(path, body=None, timeout=180):
        if path == "/api/tags":
            return {"models": tags}
        assert path == "/api/create" and body["from"] == "qwen3:4b"
        tags.append({"name": body["model"]})
        return {"status": "success"}
    with patch("app.api.studio.request", side_effect=ollama):
        form = {"name":"analyst", "base":"qwen3:4b", "instructions":"Explain arithmetic."}
        key = client.post("/studio/models/deploy", json=form).json()["id"]
        assert client.post("/studio/models/deploy", json=form).status_code == 409
        assert any(m["id"] == key and m["custom"] for m in client.get("/studio/models").json())
        with patch("app.providers.local.request", side_effect=[{"models":tags},
                   {"done":True,"message":{"content":"4"}}, {"done":True,"message":{"content":"4"}}]) as calls, patch(
                "app.ui.prompt_compare.rating", return_value={"score":10,"reason":"Correct","scope":"Test"}):
            result = client.post("/studio/prompt", json={"models":["qwen3:4b",key],"prompt":"2+2?"}).json()
        assert result["answers"][1]["judge"]["score"] == 10
        assert calls.call_args.args[1]["model"] == "modelroi/analyst:latest"
        with patch("app.providers.local.request", side_effect=[{"models":tags},
                   {"done":True,"message":{"content":"4"}}, {"done":True,"message":{"content":"4"}}]), patch(
                "app.api.studio.rating", return_value={"score":6}):
            result = client.post("/studio/benchmark", json={"models":[key,"qwen3:4b"],
                                 "suite":"analytical","count":1}).json()
        assert len(result["runs"]) == 2 and result["runs"][0]["judge_count"] == 1
