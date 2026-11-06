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
