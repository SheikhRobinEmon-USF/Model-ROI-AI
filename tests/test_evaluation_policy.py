from types import SimpleNamespace
from unittest.mock import patch

from app.evaluation_policy import Gates, rank_runs
from app.graders.exact import grade, structure_metrics
from app.graders.quality import rating
import json


def test_supported_structure_can_have_incorrect_values():
    case = SimpleNamespace(dataset_version="draft-v1", task_type="structured_extraction",
                           expected={"name": "Pat", "amount": "20"})
    output = '{"name":"Pat","amount":"30"}'
    assert not grade(case, output)["passed"]
    assert structure_metrics(case, output) == {"schema_valid": True, "field_counts": [1, 2, 2]}
    assert not structure_metrics(case, '{}')["schema_valid"]


def test_unscoped_grounding_excluded_from_mean():
    dimensions = dict(correctness=9, relevance=10, completeness=7, instruction_following=8, faithfulness=None)
    verdict = {"score": 10, "reason": "Missing a requested example.", "dimensions": dimensions}
    with patch("app.graders.quality.request", return_value={"done":True, "message":{"content":json.dumps(verdict)}}):
        assert rating("Explain X", "answer")["score"] == 8.5


def test_ineligible_fast_model_cannot_win_and_unknown_cost_excluded():
    def run(model, success, latency, cost):
        return dict(model_id=model, success_rate=success, p95_ms=latency,
                    metrics=dict(schema_rate=1, error_rate=0, provider_cost_per_success=cost))
    ranking = rank_runs([run("fast", .6, 1, None), run("accurate", 1, 50, 0)], Gates())
    assert ranking["entries"][0]["model"] == "accurate"
    assert ranking["entries"][1]["score"] is None
    assert "cost" not in ranking["weights"]
