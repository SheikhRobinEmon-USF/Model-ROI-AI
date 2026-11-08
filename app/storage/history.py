"""Local JSON run history with atomic writes and UUID-only lookup."""
from functools import lru_cache
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

@lru_cache(maxsize=1024)
def _summary(path, inode, modified, size):
    # Atomic replacement changes the file identity when a saved run is regraded.
    UUID(path.stem)
    data = json.loads(path.read_text())
    return {key: data[key] for key in ("run_id", "started_at", "model_id")}


def list_runs():
    records=[]
    for path in directory().glob('*.json'):
        try:
            stat = path.stat()
            records.append(dict(_summary(path, stat.st_ino, stat.st_mtime_ns, stat.st_size)))
        except (ValueError,KeyError,OSError):
            continue
    return sorted(records,key=lambda r:r['started_at'],reverse=True)
