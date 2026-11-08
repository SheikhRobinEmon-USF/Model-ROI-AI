from unittest.mock import patch
import pytest
from app.graders.flow import rating

def response(n):
    return {"done":True,"message":{"content":f"<feedback>Example reason.</feedback><score>{n}</score>"}}

def test_scope_and_weighting():
    with patch("app.graders.flow.request",side_effect=[response(5),response(3),response(1)]):
        assert rating("question","answer","reference")["score"] == 6.5
    with patch("app.graders.flow.request",side_effect=[response(5),response(5)]):
        verdict = rating("question","answer")
        assert verdict["score"] == 10 and "Support" not in verdict["criteria"]

def test_invalid_score():
    with patch("app.graders.flow.request",return_value=response(8)), pytest.raises(ValueError):
        rating("question","answer")
