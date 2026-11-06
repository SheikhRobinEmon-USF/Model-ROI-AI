import pytest
from fastapi.testclient import TestClient
from app.api.main import app
from app.evaluation import wilson, paired_exact, percentile, run_demo, mock_answer

def test_wilson_reference():
    assert wilson(18,20) == pytest.approx([.69896,.97213], abs=.0001)

def test_exact_reference():
    assert paired_exact(6,1) == .125
    assert paired_exact(0,0) == 1

def test_percentile():
    assert percentile(list(range(1,51)),.95) == 48

def test_demo():
    result = run_demo()
    assert len(result['results']) == 5
    assert result['evidence_type'] == 'synthetic_mock'
    assert result['recommendation_status'] != 'CERTIFIED'

def test_classifier_unseen():
    assert mock_answer('This is terrible') == 'negative'
    assert mock_answer('A shipment') == 'neutral'

def test_api():
    client = TestClient(app)
    assert client.get('/health').status_code == 200
    assert client.get('/v1/demo').json()['attempted_cases'] == 5
    assert client.post('/v1/runs').status_code == 403

@pytest.mark.parametrize('successes,n',[(-1,5),(6,5)])
def test_invalid_counts(successes,n):
    with pytest.raises(ValueError):
        wilson(successes,n)
