from unittest.mock import patch
import pytest
from app.graders.qwen import JUDGE, rating

def test_judge_controls_the_displayed_score():
    response = {"done": True, "message": {"content": '{"score":8,"reason":"One calculation is missing."}'}}
    with patch("app.graders.qwen.request", return_value=response) as call:
        verdict = rating("Estimate the total.", "The total is 14.")
    assert verdict["score"] == 8 and verdict["model"] == JUDGE
    payload = call.call_args.args[1]
    assert payload["model"] == "qwen3.8:27b"
    assert "The total is 14." in payload["messages"][1]["content"]

@pytest.mark.parametrize("invalid", ["true","11","-1","8.5"])
def test_invalid_scores_stay_unscored(invalid):
    with patch("app.graders.qwen.request", return_value={"done":True,"message":{"content":'{"score":'+invalid+',"reason":"ok"}'}}):
        with pytest.raises(ValueError):
            rating("question","answer")
