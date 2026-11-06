"""Local JSON run history with atomic writes and UUID-only lookup."""
import json
import os
from pathlib import Path
from uuid import UUID
import tempfile

def directory():
    path=Path(os.environ.get('MODELROI_HISTORY_DIR',str(Path.home()/'.modelroi'/'runs')))
    path.mkdir(parents=True,exist_ok=True,mode=0o700)
    return path

def save(result):
    run_id=str(UUID(result['run_id']))
    folder=directory()
    fd,name=tempfile.mkstemp(dir=folder,suffix='.tmp')
    try:
        with os.fdopen(fd,'w') as f:
            json.dump(result,f,indent=2,allow_nan=False)
        os.replace(name,folder/f'{run_id}.json')
    finally:
        if os.path.exists(name):
            os.unlink(name)
    return run_id

def load(run_id):
    return json.loads((directory()/f'{UUID(run_id)}.json').read_text())

def list_runs():
    records=[]
    for path in directory().glob('*.json'):
        try:
            data=load(path.stem)
            records.append({'run_id':data['run_id'],'started_at':data['started_at'],'model_id':data['model_id']})
        except (ValueError,KeyError,OSError):
            continue
    return sorted(records,key=lambda r:r['started_at'],reverse=True)
