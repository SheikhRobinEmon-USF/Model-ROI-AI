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

## Additional components
- Persistent DuckDB reservation ledger with serialized transactions, cancellation, retained unknown liabilities, and restart tests. Not yet connected to paid execution.
- 50 draft synthetic cases (20 extraction, 20 hospital arithmetic, 10 classification), marked pending human review.
- Strict JSONL import validation and exact typed JSON graders.
- 68 passing tests as of this increment. This count includes 50 parametrized draft-case checks and does not establish production readiness.

## Free local model direction

Paid APIs are not authorized. Follow [SETUP.md](SETUP.md) for Windows, macOS and Linux instructions, Hugging Face/Ollama models, hardware guidance and the local inference probe. The probe is separate from the mock dashboard; local integration is not yet a completed release.
