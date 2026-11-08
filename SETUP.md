# Free local model setup: Windows, macOS, Linux

Policy updated November 6, 2026: no paid APIs. Use local downloadable weights with Ollama. Hugging Face is the model source; local computation uses your own RAM, CPU/GPU and electricity. Hosted inference is not automatically free because weights are downloadable.

## Studio models

| Ollama tag | Role |
|---|---|
| `qwen3:4b` | First answer |
| `gemma4:e4b` | Second answer |
| `gpt-oss:20b` | Quality grades, comments and comparison summaries |

The studio runs inference sequentially. On a 16 GB Mac the judge competes with macOS and other apps for unified memory. Response time depends on the prompt and available memory.

## 1. Install prerequisites

Install Git and Python 3.12. Install Ollama from https://ollama.com/download.

### Windows (PowerShell)

Ollama supports Windows 10 22H2 or newer. Install the native Windows application and open it. Install current GPU drivers if using acceleration. No WSL is required.

```powershell
git clone https://github.com/SheikhRobinEmon-USF/Model-ROI-AI.git
cd Model-ROI-AI
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest -q
```

Using the environment's Python directly avoids PowerShell activation-policy changes.

### macOS (Terminal)

Ollama requires macOS 14 or newer. Apple Silicon supports GPU acceleration; Intel Macs use CPU. Download the DMG, move Ollama to Applications, and open it.

```bash
git clone https://github.com/SheikhRobinEmon-USF/Model-ROI-AI.git
cd Model-ROI-AI
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest -q
```

### Linux (Terminal)

Install Git, Python 3.12 and its venv package using your distribution's package manager. Download and inspect Ollama's installer, then run it:

```bash
curl -fsSL https://ollama.com/install.sh -o /tmp/ollama-install.sh
less /tmp/ollama-install.sh
sh /tmp/ollama-install.sh
git clone https://github.com/SheikhRobinEmon-USF/Model-ROI-AI.git
cd Model-ROI-AI
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest -q
```

If the Ollama service is not running, run `ollama serve` in another terminal. GPU support depends on your driver/hardware; see https://docs.ollama.com/gpu.

## 2. Download local models (same commands on all three systems)

```text
ollama pull qwen3:4b
ollama pull gemma4:e4b
ollama pull gpt-oss:20b
ollama list
ollama run qwen3:4b
```

Optional lower-memory model: `ollama pull qwen3:1.7b`.

For a model downloaded directly from the official Hugging Face GGUF repository:

```text
ollama run hf.co/Qwen/Qwen3-4B-GGUF:Q8_0
```

Q8 uses more memory than the default quantized Ollama tag. Hugging Face Transformers/safetensors repositories are not interchangeable with GGUF repositories. Only use the GGUF command for compatible artifacts. The Ollama-library route and HF route can use different quantizations; record that difference in benchmark results.

## 3. Verify local inference through this project

Windows:
```powershell
.\.venv\Scripts\python.exe -m app.providers.local --model qwen3:4b
```
macOS/Linux (activated environment):
```bash
python -m app.providers.local --model qwen3:4b
```

The probe calls only `127.0.0.1:11434`, never a paid provider. Models must already be downloaded. This is an inference probe, not a complete benchmark. It records the installed model digest when available. Do not claim cross-machine reproducibility without recording Ollama version, hardware, quantization and settings as well.

## 4. Start the existing offline dashboard

Windows:
```powershell
.\.venv\Scripts\python.exe -m streamlit run app/ui/Home.py
```
macOS/Linux:
```bash
python -m streamlit run app/ui/Home.py
```

Open http://localhost:8501. The current dashboard still runs the five-case mock; the local probe is separate. Full local-model benchmark/dashboard integration remains unfinished. Paid routes remain disabled.

## Troubleshooting and deployment

- Connection refused: open Ollama or run `ollama serve`; ensure port 11434 is available.
- Model not found: run the matching `ollama pull` command and inspect `ollama list`.
- Out of memory: use 1.7B, close other apps, keep context short and run sequentially.
- Slow output: CPU-only inference can be slow; compare measured latency on the actual host.
- Container localhost points to the container, not the host. This probe is intentionally for native execution; Docker networking for local inference is not implemented.
- Keep Ollama bound to localhost. Do not expose its unauthenticated API publicly.
- For 10–15 monthly testers, publish recorded local benchmark results and let visitors explore the offline interface. Live inference requires an always-on host; free model weights do not supply free hosting.
- The old two-paid-provider release gate is superseded by the user's no-paid-API direction. A local-model release must be labeled as such, with actual local evidence still required.

## Sources checked November 6, 2026

- https://huggingface.co/Qwen/Qwen3-4B
- https://huggingface.co/Qwen/Qwen3-4B-GGUF
- https://huggingface.co/docs/hub/ollama
- https://ollama.com/library/qwen3
- https://docs.ollama.com/windows
- https://docs.ollama.com/macos
- https://docs.ollama.com/linux
- https://docs.ollama.com/api/chat

## Integrated local interface (latest update)

The Prompt lab and Benchmark pages now support Qwen3 through Ollama when explicitly enabled. Native installation is recommended. Before starting Streamlit:

Windows PowerShell: `$env:MODELROI_ENABLE_LOCAL="true"`

macOS/Linux: `export MODELROI_ENABLE_LOCAL=true`

Then run the Streamlit command above. Select Prompt lab to test a prompt, Benchmark to evaluate 1–50 cases, and Results to inspect failures and export JSON/CSV. Public deployments must leave this variable unset/false. Local inference runs on the server hosting Streamlit, not in a visitor's browser. Local benchmark results are persisted under ~/.modelroi/runs; prompt-lab and mock results remain temporary.

This section supersedes earlier statements that the local probe is separate from the dashboard. No real model run has been verified in the development container, which does not have Ollama installed.

## Simplified launcher for your existing Ollama installation

Open Ollama, clone/download this repository, and open a terminal in the repository folder. Run:

- Windows: `py -3.12 scripts/start_local.py`
- macOS/Linux: `python3.12 scripts/start_local.py`

The launcher checks the local Ollama service, asks before a missing Qwen3 download, creates an isolated Python environment, installs application dependencies, and starts the interface bound to localhost. Keep the terminal open while using the app. It makes no paid API calls. Downloading Python packages and missing model weights requires internet access.

ChatGPT's remote workspace cannot automatically reach Ollama on your personal computer. Running this launcher locally is the supported bridge; you do not need to open firewall ports or share API credentials.

## Updating the redesigned interface on macOS

Stop the running app with Control+C. If your folder was downloaded as a ZIP (`Model-ROI-AI-main`), download the current ZIP again and extract it to a new folder; `git pull` only works in a Git clone. Preserve your existing folder until the new version starts. Saved runs remain in `~/.modelroi/runs`.

For a Git clone, run `git pull --ff-only` and restart with `python3 scripts/start_local.py` using Python 3.12 or newer. Open the printed URL. The launcher serves the bundled browser interface without a Node installation.

## Compare two local models

With Ollama running, install `gemma4:e4b` using `ollama pull` for each tag. Qwen uses `qwen3:4b`. In Benchmark leave both selected, choose five cases for a quick check, run the benchmark, then open Results. All categories cycles through workloads so small samples cover multiple task types. Each model receives the same selected inputs. The saved comparison includes every answer and grade.

## Share a live tester session from your Mac

Open Ollama and keep the Mac awake. In your Git clone, run `brew install cloudflared` once, then `python3 scripts/start_pilot.py`. This uses the existing .venv from the local launcher. Share the printed HTTPS trycloudflare.com link and tester code privately. Keep Terminal running; Control+C ends the session. Each restart creates a new code and temporary link. The tester interface handles one prompt comparison at a time and holds results in the visitor's session. A Quick Tunnel is a development/testing service. Hosting and model API fees are zero; your computer and network supply inference.

### Automatic quality judge
Run `ollama pull gpt-oss:20b`. The judge grades each delivered answer directly from 0 to 10 and explains the score. Historical reports keep their original grades.

### Local storage and migration

The first history read imports valid legacy UUID-named JSON reports into `history.sqlite3` in `~/.modelroi/runs` (or `MODELROI_HISTORY_DIR`). New writes go to SQLite. Old JSON files remain as migration originals; deleting an imported conversation also removes its corresponding original files. For a complete backup, stop the studio and copy the history directory. Restart with that directory to restore it.

Open History and choose **Analyze saved benchmarks** to run DuckDB locally on the benchmark measurements. The analytical database exists only for that query. No separate server, account or network extension is required.

### Longer follow-up context on macOS

The default launcher uses extended mode. Run `python3 scripts/start_local.py` to include up to 12 earlier turns and 8,000 characters of combined history per candidate. A follow-up carrying history requests an 8,192-token window from Ollama. Standard mode uses six turns, 3,200 characters and 4,096 tokens. Prior user questions are individually capped at 2,000 characters in extended mode and 800 in standard mode. Recent turns take priority. The full saved transcript stays available in both modes. Use `MODELROI_CHAT_CONTEXT=standard python3 scripts/start_local.py` for the smaller memory budget.

## Hosted API mode

Use free-tier projects with billing disabled or a provider-side spending cap where available. The studio uses fixed routes and has no paid-model fallback. An API key attached to a billed account can incur provider charges. Verify the account tier before running a workload.

Configure credentials in the environment of the launcher. On macOS zsh, for example, use `read -rs "GROQ_API_KEY?Groq key: "; export GROQ_API_KEY` to enter a key privately. Repeat with the appropriate variable for each selected service. Keys stay on the FastAPI server. Do not commit keys or paste them into chat.

| Provider | Server variable | Hosted responder |
|---|---|---|
| Google Gemini | GEMINI_API_KEY | gemini-3.5-flash-lite |
| Groq | GROQ_API_KEY | qwen/qwen3.8-27b |
| OpenRouter | OPENROUTER_API_KEY | google/gemma-4-26b-a4b-it:free |
| Mistral | MISTRAL_API_KEY | mistral-small-latest |
| Cloudflare | CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID | @cf/meta/llama-3.3-70b-instruct-fp8-fast |

The Groq key also enables the independent judge and Results summary (`openai/gpt-oss-120b`). Use a Cloudflare token scoped to Workers AI. From the clone, run `python3 scripts/start_local.py --hosted` (Windows: `py -3.12 scripts/start_local.py --hosted`) to skip Ollama startup checks. Select **Hosted**, then **Models**. Ready means credentials are configured; account access is checked when a request runs.

Providers receive the current prompt, shared excerpts and their own prior conversation. Grading sends the answer, task, relevant context and optional reference to Groq. The summary sends labeled report evidence to Groq. The longer history option considers up to 32 turns and 24,000 characters per responder, subject to service quotas. By default history uses the common local comparison budget. A candidate newly added mid-chat has no earlier answers of its own.

Start with one prompt before a benchmark. Dispatch is sequential and answers appear individually. End-to-end timings include network and provider processing. A short provider-supplied Retry-After on HTTP 429 is retried once. Regrade saved prompt answers if the judge quota expires. Quotas, availability and aliases can change; Mistral's latest alias can change its underlying revision.
