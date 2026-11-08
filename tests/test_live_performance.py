import json
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.api.main import app
from app.ui.comparison import MODELS
from app.providers.local import generate
from app.execution.performance import run_scope


@pytest.mark.parametrize("texts,scores", [(("a","a"), [7,7]), (("a","b"), [7,8])])
def test_answers_precede_grading_and_only_identical_verdicts_reused(tmp_path,monkeypatch,texts,scores):
    monkeypatch.setenv('MODELROI_ENABLE_LOCAL','true')
    monkeypatch.setenv('MODELROI_HISTORY_DIR',str(tmp_path))
    client=TestClient(app,base_url='http://127.0.0.1')
    outputs=[dict(output=text,latency_ms=5) for text in texts]
    with patch('app.ui.prompt_compare.generate',side_effect=outputs), patch(
        'app.ui.prompt_compare.rating',side_effect=lambda q,a:dict(score=7 if a=='a' else 8,scope='test')) as judge:
        response=client.post('/studio/live/prompt',json=dict(prompt='x',models=list(MODELS)),
                             headers={'origin':'http://127.0.0.1'})
    events=[json.loads(line) for line in response.text.splitlines()]
    answers=[e['row'] for e in events if e['event']=='answer']
    assert all('judge' not in r for r in answers[:2])
    assert judge.call_count==len(set(texts))
    assert [r['judge']['score'] for r in events[-1]['report']['answers']]==scores
    assert events[-1]['event']=='complete'


def test_inventory_fetched_once_but_every_case_runs():
    tags={'models':[{'name':'qwen3:4b','digest':'abc'}]}
    def fake(path,body=None):
        return tags if path.endswith('tags') else {'done':True,'message':{'content':'answer'}}
    with run_scope(), patch('app.providers.local.request',side_effect=fake) as requests:
        for _ in range(50):
            generate('qwen3:4b','sample')
    assert [c.args[0] for c in requests.call_args_list].count('/api/tags')==1
    assert [c.args[0] for c in requests.call_args_list].count('/api/chat')==50
