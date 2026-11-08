from unittest.mock import patch
from fastapi.testclient import TestClient
from app.api.main import app
from app.graders.flow import rating

def test_private_studio_and_partial_grading(tmp_path,monkeypatch):
    monkeypatch.setenv("MODELROI_ENABLE_LOCAL","true")
    monkeypatch.setenv("MODELROI_HISTORY_DIR",str(tmp_path))
    client=TestClient(app,base_url="http://127.0.0.1")
    payload={"prompt":"Example","models":["qwen3:4b"]}
    assert client.post("/studio/prompt",json=payload).status_code==403
    with patch("app.ui.prompt_compare.generate",return_value={"output":"unfinished idea","done_reason":"length","latency_ms":123}), patch("app.ui.prompt_compare.rating",return_value={"score":5,"scope":"Clarity","criteria":{}}):
        result=client.post("/studio/prompt",json=payload,headers={"origin":"http://127.0.0.1"}).json()
    assert result["answers"][0]["judge"]["scope"].endswith("(partial answer)")
    assert client.get("/studio/history").json()[0]["run_id"]==result["run_id"]
    assert "ModelROI" in client.get("/").text

def test_judge_retries_with_schema():
    malformed={"done":True,"message":{"content":"Explanation without tags"}}
    valid={"done":True,"message":{"content":'{"score":4,"feedback":"Answered clearly"}'}}
    with patch("app.graders.flow.request",side_effect=[malformed,valid,malformed,valid]) as call:
        assert rating("question","answer")["score"]==7.5
        assert "format" in call.call_args.args[1]
