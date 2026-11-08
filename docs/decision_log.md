# Engineering decisions

## Local evaluation studio

Two local candidates share each task. An independent local gpt-oss-20b supplies a grade and short comment. Deterministic benchmark checks remain separate. Summaries are requested on opening Results and cached to reduce judge work. The browser tracks server-reported phases and case counts without estimating model completion times. Conversations and their management metadata reside in local run history.

## Historical budget ledger design
DuckDB remains the planned storage engine. A single API process owns its connection; threads serialize transactions with an RLock. Streamlit must use the API for persisted writes. Multi-worker Uvicorn is unsupported for this design. Source: https://duckdb.org/docs/stable/connect/concurrency (reviewed 2026-11-06).

Reservations retain unknown usage liability across restarts and cancellation. This module is not yet wired to a provider runner. Per-owner daily quotas and attempt audit history remain required before enabling paid execution.

## SDK retry ownership
The future provider runner must disable SDK automatic retries and record every attempt itself, because otherwise retry costs are hidden from the ledger. Source: https://github.com/openai/openai-python (reviewed 2026-11-06).
