from fastapi import FastAPI, HTTPException
from app.evaluation import run_demo
app = FastAPI(title='ModelROI AI', version='0.1.0')

@app.get('/health')
def health():
    return {'status': 'ok', 'schema_version': '1', 'mode': 'offline_mock'}

@app.get('/v1/demo')
def demo():
    return run_demo()

@app.post('/v1/runs')
def paid_run():
    raise HTTPException(403, 'Paid execution is unavailable in this offline preview.')

from pathlib import Path
from fastapi.staticfiles import StaticFiles
from app.api.studio import router

app.include_router(router)
bundle = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if bundle.is_dir():
    app.mount("/", StaticFiles(directory=bundle, html=True), name="studio")
