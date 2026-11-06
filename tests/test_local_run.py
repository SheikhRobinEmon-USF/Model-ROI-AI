from app.execution.local_run import run
from app.datasets.validate import EvalCase

def case():
    return EvalCase(case_id='a',task_type='structured_extraction',input='x',expected={'amount':'1.00'},grader='json_exact',dataset_version='v1',source_license='original_synthetic',split='dev',review_status='pending_human_review')

def test_records_success_and_hash():
    result=run([case()],generate_fn=lambda *a:dict(output='{"amount":"1.00"}',latency_ms=10,done_reason='stop'))
    assert result['successful_cases']==1
    assert len(result['dataset_sha256'])==64
    assert result['total_compute_cost_usd'] is None

def test_failure_is_not_dropped():
    def fail(*a):
        raise TimeoutError()
    result=run([case()],generate_fn=fail)
    assert result['attempted_cases']==1
    assert result['successful_cases']==0
    assert result['results'][0]['error_type']=='TimeoutError'

def test_truncated_answer_fails():
    result=run([case()],generate_fn=lambda *a:dict(output='{"amount":"1.00"}',latency_ms=10,done_reason='length'))
    assert result['successful_cases']==0
