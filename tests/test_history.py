from uuid import uuid4
import pytest
from app.storage.history import save,load,list_runs

def test_history_survives_reload(tmp_path,monkeypatch):
    monkeypatch.setenv('MODELROI_HISTORY_DIR',str(tmp_path))
    data={'run_id':str(uuid4()),'started_at':'2026-11-06','model_id':'qwen3:4b','results':[]}
    save(data)
    assert load(data['run_id'])==data
    assert len(list_runs())==1

def test_no_path_traversal():
    with pytest.raises(ValueError):
        load('../../etc/passwd')


def test_legacy_migration_and_duckdb_metrics(tmp_path, monkeypatch):
    import json
    from app.storage.history import benchmark_analytics
    monkeypatch.setenv("MODELROI_HISTORY_DIR", str(tmp_path))
    key = str(uuid4())
    run = {"run_id": key, "model_id": "qwen3:4b", "started_at": "2026-11-08", "results": [
        {"passed": True, "status": "completed", "judge": {"score": 0}, "latency_ms": 200},
        {"passed": False, "status": "failed", "latency_ms": 900}]}
    (tmp_path / f"{key}.json").write_text(json.dumps(run))
    assert load(key) == run
    run["results"][0]["judge"]["score"] = 8
    save(run)
    assert benchmark_analytics() == [dict(model="qwen3:4b", runs=1, attempts=2, passed=1,
                                         graded=1, mean_grade=8, median_ms=200)]
    assert load(key) == run
