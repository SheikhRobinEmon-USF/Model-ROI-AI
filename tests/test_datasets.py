from pathlib import Path
import json
import pytest
from app.datasets.validate import validate_jsonl
from app.graders.exact import grade

def cases():
    return validate_jsonl((Path(__file__).parents[1]/'datasets/v1/draft_cases.jsonl').read_bytes())

def test_composition():
    rows=cases()
    assert len(rows)==50
    assert sum(r.task_type=='hospital_finance_qa' for r in rows)==20
    assert all(r.review_status=='pending_human_review' for r in rows)

@pytest.mark.parametrize('index',range(50))
def test_gold_and_corruption(index):
    case=cases()[index]
    assert grade(case,json.dumps(case.expected))['passed']
    assert not grade(case,'{}')['passed']
    assert not grade(case,'not json')['passed']

def test_duplicate_rejected():
    row=cases()[0].model_dump_json()
    with pytest.raises(ValueError,match='Duplicate'):
        validate_jsonl((row+'\n'+row).encode())
