# ModelROI AI

A local-first evaluation studio for Qwen3 4B. Test prompts, evaluate structured workloads, inspect failures, and download the evidence behind each result.

**Status: functional development preview, not a validated production release.** Paid APIs are disabled. Real Qwen3 inference has not yet been verified in the development environment. The dataset contains 50 draft synthetic cases pending independent review.

## Quick start

Install Python 3.12, Git and Ollama, then:

```bash
git clone https://github.com/SheikhRobinEmon-USF/Model-ROI-AI.git
cd Model-ROI-AI
python -m venv .venv
# Activate the environment as described in SETUP.md.
python -m pip install -e '.[dev]'
ollama pull qwen3:4b
```

Enable local execution in your terminal:
- macOS/Linux: `export MODELROI_ENABLE_LOCAL=true`
- Windows PowerShell: `$env:MODELROI_ENABLE_LOCAL="true"`

Run `python -m streamlit run app/ui/Home.py` and open http://localhost:8501.

[Complete Windows, macOS and Linux setup](SETUP.md)

## Interface

- **Overview:** workload summary and instant no-model mock demo.
- **Prompt lab:** test a bounded prompt against Qwen3 on the host computer.
- **Benchmark:** select task category and 1–50 cases; run sequentially.
- **Results:** inspect success counts, Wilson intervals, failures, expected answers and outputs; download JSON/CSV.

The public preview defaults to mock-only mode. Never enable local execution on an unrestricted public server. For a small visitor pilot, use the mock preview until reviewed historical results and publication controls are implemented.

## Evidence and methodology

The local runner records model digest when supplied by Ollama, dataset SHA-256, settings, token counts, UTC start time and per-case elapsed time. Exceptions count as failed cases. Truncated outputs fail grading. Exact JSON checks preserve types; numeric 1 does not equal boolean true.

A 95% Wilson interval accompanies success rates. Latency is machine-specific and exploratory with fewer than 100 observations. No comparative model winner is claimed. Zero provider API fees do not imply zero electricity or hardware cost.

Hospital cases are synthetic arithmetic examples, not independently verified CMS facts. The current graders do not implement the entire financial grounding specification. Local benchmark runs are saved atomically under ~/.modelroi/runs and can be reopened from Results. Prompt-lab and mock results remain session-only.

## Architecture

Streamlit calls a local sequential evaluation service, which uses the localhost Ollama API and deterministic graders. FastAPI currently provides health and mock-demo endpoints; it does not orchestrate local runs. DuckDB reservation infrastructure is retained for future work but paid execution is unavailable.

## Validation

```bash
python -m pytest -q
python -m app.providers.local --model qwen3:4b
```

The second command requires Ollama and downloaded weights. Simulated provider tests are not evidence of actual model performance. Docker Compose starts the mock UI/API preview; native installation is the documented local-model path.

## Remaining release gates

- Actual Qwen3 run and reviewed output evidence on target hardware.
- Independently reviewed, diverse labels and untouched holdout.
- Full financial/citation/refusal graders and recommendation policy.
- Cancellation, report sanitization and validated external historical-run import.
- Reproducible dependency locking, container verification, cross-platform CI and public deployment checks.

## License

Original application code is MIT licensed. Qwen3 4B model artifacts retain their Apache 2.0 license and are downloaded separately. See https://huggingface.co/Qwen/Qwen3-4B/blob/main/LICENSE. Model weights are not bundled with this repository.

The original v2.1 contract remains in docs/implementation_contract.md. The user's subsequent decision to use free local Qwen3 supersedes its paid-provider release requirement; other unmet requirements remain explicitly tracked above.

## Launch with existing Ollama

Open Ollama, then run `python3.12 scripts/start_local.py` on macOS/Linux or `py -3.12 scripts/start_local.py` on Windows. The launcher installs application dependencies and starts the private local interface.

### Three-model benchmark
Compare Qwen3 4B, Gemma 4 E4B and Phi-4-mini on matched cases. Benchmark supports one to three models. Results for multi-model runs include pass rates, median response times, case-level disagreements, side-by-side answers, Wilson intervals and Holm-adjusted exact paired tests. All execution is local.

### Analytical challenges and file questions

In **Benchmark → Analytical challenges**, compare six scored math, code-tracing/debugging and operations problems. Choose a category or run the whole set. Each problem asks for a JSON answer with explicit fields. The same deterministic answer key grades every model. Use Results to inspect misses and uncertainty.

In **Prompt lab** or **Benchmark → My question**, upload a file, enter a question, preview the excerpt and compare responses. The local launcher installs PDF, modern Office and Excel readers. Legacy binary Word/PowerPoint files require antiword/catppt respectively, or conversion to DOCX/PPTX. Scanned PDFs require prior OCR. Only the displayed excerpt is sent to each model. Local history includes the excerpt. File questions are qualitative unless a separate graded workload is selected.

## Local web studio
The Mac/Windows/Linux launcher now serves a compiled Svelte 5 + TypeScript studio from FastAPI. Run `python3 scripts/start_local.py` after updating your clone. Use the URL printed by the launcher. The browser bundle is included and runs without a Node installation or CDN. The previous Streamlit workspace remains available using the manual instructions in SETUP.md. The tester pilot remains a separate entry point.

Frontend development: from `frontend/`, run `npm ci` and `npm run build`; commit the generated dist folder with source changes.
