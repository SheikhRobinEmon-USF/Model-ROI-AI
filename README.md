# ModelROI AI

Outcome-based model evaluation and cost intelligence.

## Current status
Working offline foundation preview. This is not a completed MVP. It evaluates five synthetic sentiment cases with a deterministic mock, displays Wilson intervals, and exports the full evidence. Mock timings are not real model latency. Paid execution is disabled.

## Run locally
```bash
pip install -e '.[dev]'
pytest -q
python -m app.evaluation
streamlit run app/ui/Home.py
# Separate terminal:
uvicorn app.api.main:app
```
Or run `docker compose up --build`, then visit http://localhost:8501 (UI) and http://localhost:8000/docs (API).

## Remaining release requirements
50 reviewed cases and separate holdout; full graders; two provider adapters; persistent transactional spending reservations; cancellation/retry accounting; complete decision engine; comparison/failure/report UI; actual authorized two-provider benchmark; public hosted demo. See [the approved implementation contract](docs/implementation_contract.md).

No provider performance, adoption, or realized ROI is claimed. MIT licensed.
