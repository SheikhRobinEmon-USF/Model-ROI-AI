"""Strict import boundary for nonconfidential evaluation cases."""
import json
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class EvalCase(BaseModel):
    model_config = ConfigDict(extra='forbid')
    case_id: str = Field(min_length=1, max_length=100, pattern=r'^[a-zA-Z0-9_-]+$')
    task_type: Literal['structured_extraction','hospital_finance_qa','instruction_following_classification','math','coding','case_study']
    input: str = Field(min_length=1,max_length=20000)
    expected: dict
    grader: Literal['json_exact','classification_exact']
    dataset_version: str
    source_license: str
    split: Literal['dev','holdout']
    review_status: Literal['pending_human_review','reviewed']

def validate_jsonl(raw: bytes):
    if len(raw) > 2_000_000:
        raise ValueError('Dataset exceeds 2 MB')
    rows = [EvalCase.model_validate(json.loads(line)) for line in raw.decode('utf-8').splitlines() if line.strip()]
    if not 1 <= len(rows) <= 1000:
        raise ValueError('Require 1–1000 cases')
    if len({row.case_id for row in rows}) != len(rows):
        raise ValueError('Duplicate case IDs')
    return rows
