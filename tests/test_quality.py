import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.graders.quality import MODEL, rating


def reply(content):
    return {"done": True, "message": {"content": json.dumps(content)}}


@pytest.mark.parametrize("score", range(11))
def test_every_grade(score):
    with patch("app.graders.quality.request", return_value=reply({"score": score, "reason": " Clear. "})) as call:
        result = rating("Question", "Answer")
    assert (result["score"], result["reason"], result["model"]) == (score, "Clear.", MODEL)
    assert call.call_count == 1
    assert call.call_args.args[1]["model"] == MODEL


@pytest.mark.parametrize("invalid", [None, [], {"score": True, "reason": "yes"},
    {"score": 11, "reason": "yes"}, {"score": -1, "reason": "yes"}, {"score": 7, "reason": " "},
    {"score": "8/20", "reason": "yes"}])
def test_invalid_verdict_retried_then_rejected(invalid):
    with patch("app.graders.quality.request", return_value=reply(invalid)) as call:
        with pytest.raises(ValueError, match="two attempts"):
            rating("q", "a")
        assert call.call_count == 2


def test_live_grading_and_saved_retry(tmp_path, monkeypatch):
    monkeypatch.setenv("MODELROI_ENABLE_LOCAL", "true")
    monkeypatch.setenv("MODELROI_HISTORY_DIR", str(tmp_path))
    client = TestClient(app, base_url="http://127.0.0.1", headers={"origin": "http://127.0.0.1"})
    models = ["qwen3:4b", "gemma4:e4b"]
    prompt = {"models": models, "prompt": "What is 2 + 2?"}
    assert client.post("/studio/prompt", json={**prompt, "models": ["phi4-mini:3.8b"]}).status_code == 422
    valid = reply({"score": 10, "reason": "The sum is correct."})
    with patch("app.ui.prompt_compare.generate", side_effect=[{"output": "4"}, {"output": "Four"}]), patch(
        "app.graders.quality.request", side_effect=[TimeoutError(), {"done": False}, valid]
    ):
        events = [json.loads(line) for line in client.post("/studio/live/prompt", json=prompt).text.splitlines()]
    report = events[-1]["report"]
    first, second = report["answers"]
    assert "judge_error" in first and "judge" not in first
    assert second["judge"]["score"] == 10
    path = "/studio/history/" + report["run_id"]
    with patch("app.graders.quality.request", return_value=valid) as judge:
        graded = client.post(path + "/grade").json()
    assert judge.call_count == 1
    assert graded == client.get(path).json()
    assert all(row["judge"]["reason"] == "The sum is correct." and "judge_error" not in row for row in graded["answers"])


@pytest.mark.parametrize(("score", "key"), [("8", "reason"), ("8/10", "comment"), (8.0, "feedback")])
def test_equivalent_verdicts(score, key):
    with patch("app.graders.quality.request", return_value=reply({"score": score, key: "Mostly correct."})) as call:
        assert rating("q", "a")["score"] == 8
        assert call.call_count == 1


def test_empty_comment_triggers_targeted_repair():
    with patch("app.graders.quality.request", side_effect=[reply({"score": 4, "reason": ""}),
               reply({"score": 4, "reason": "Missing the date."})]) as call:
        assert rating("q", "a")["reason"] == "Missing the date."
        assert "nonempty sentence" in call.call_args.args[1]["messages"][-1]["content"]
