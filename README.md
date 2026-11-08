# ModelROI AI

ModelROI compares Qwen3 4B and Gemma 4 E4B on the same question or benchmark using Ollama on your computer. OpenAI’s local gpt-oss-20b grades delivered answers and summarizes each comparison. The studio is a development preview with 50 draft synthetic benchmark cases.

## Start the studio

Install Git, Ollama and Python 3.12 or newer. Open Ollama, then run:

```bash
git clone https://github.com/SheikhRobinEmon-USF/Model-ROI-AI.git
cd Model-ROI-AI
ollama pull qwen3:4b
ollama pull gemma4:e4b
ollama pull gpt-oss:20b
python3 scripts/start_local.py
```

On Windows use `py -3.12 scripts/start_local.py` for the last command. Open the printed local URL. To update a clone, stop the launcher, run `git pull --ff-only` and restart it. [Platform setup and optional tester pilot](SETUP.md)

## Using the studio

- **Prompt lab** compares prompts or extracted document excerpts. Send a follow-up with Enter or insert a newline with Shift+Enter. Each candidate receives bounded context from its own prior answers.
- **Processing** follows actual server events through preparation, generation, grading and saving. It names the active model or benchmark case when available. Answers appear as each candidate finishes. Expand **Metrics** below an answer for timing, the judge’s grade out of 10 and its comment. Failed grades can be retried on saved answers.
- **Chats** keeps conversations in the left sidebar, with a history toggle on mobile. New chat starts a separate thread. Use the actions menu to rename, pin, unpin or delete one.
- **Benchmark** runs one or both candidates on matched cases, including six analytical challenges in math, coding and operations. Executable scoring checks expected JSON alongside the judge’s qualitative assessment.
- **Results** shows a short comparison generated when first opened and cached locally. Inspect case-level evidence, grades, timings and uncertainty, or export the report as JSON. **History** reopens saved runs.

## Architecture and evidence

The launcher serves a bundled Svelte and TypeScript frontend from FastAPI. The API streams progress and results over newline-delimited JSON. Ollama runs models sequentially to limit memory pressure. Completed prompt turns and benchmarks are stored under `~/.modelroi/runs`, including submitted excerpts. Public hosting is deferred.

The local runner records model digest when supplied by Ollama, dataset SHA-256, settings, token counts, UTC start time and per-case elapsed time. Exceptions count as failed cases. Truncated outputs fail grading. Exact JSON checks preserve types; numeric 1 does not equal boolean true.

A 95% Wilson interval accompanies success rates. Latency is machine-specific and exploratory with fewer than 100 observations. No comparative model winner is claimed. Zero provider API fees do not imply zero electricity or hardware cost.

Hospital cases are synthetic arithmetic examples, not independently verified CMS facts. The current graders do not implement the entire financial grounding specification. Local benchmark runs are saved atomically under ~/.modelroi/runs and can be reopened from Results. The studio also saves prompt comparisons.

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

For the active implementation plan and historical baseline see [the implementation contract](docs/implementation_contract.md). For frontend development run `npm ci` and `npm run build` in `frontend/`, then commit the rebuilt bundle.
