import json
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.api.main import app
from app.providers import hosted


def test_hosted_run_and_judge(tmp_path, monkeypatch):
    monkeypatch.setenv("MODELROI_ENABLE_LOCAL", "true")
    monkeypatch.setenv("MODELROI_HISTORY_DIR", str(tmp_path))
    client = TestClient(app, base_url="http://127.0.0.1", headers={"origin":"http://127.0.0.1"})
    def completion(model, messages, limit, schema=None):
        text = "Blue"
        if model == hosted.JUDGE:
            text = json.dumps({"score":9,"reason":"Specific."}) if schema else "The responses agree."
        else:
            assert "Reference only" not in str(messages)
        return {"finish_reason":"stop","message":{"content":text}}, {"model":model}
    with patch.object(hosted, "completion", side_effect=completion):
        report = client.post("/studio/prompt", json={"models":list(hosted.ROUTES),"prompt":"Color?",
            "reference_answer":"Reference only","long_context":True}).json()
        assert len(report["answers"]) == 5
        assert all(r["judge"]["model"] == hosted.JUDGE for r in report["answers"])
        summary = client.post("/studio/history/"+report["run_id"]+"/summary").json()
        assert summary["model"] == hosted.JUDGE
        result = client.post("/studio/benchmark", json={"suite":"analytical","count":1,"models":list(hosted.ROUTES)}).json()
        assert len(result["runs"]) == 5 and len(result["pairs"]) == 10
