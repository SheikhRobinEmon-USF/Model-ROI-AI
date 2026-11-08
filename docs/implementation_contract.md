# MODELROI AI
## Final Product Strategy, Engineering, Evaluation and Launch Plan

## Current implementation plan · November 2026

The current studio implements local Qwen3 and Gemma comparisons, a separate gpt-oss-20b judge, streamed progress for generation and grading, and local report storage. Chat threads support follow-ups, attachments, rename, pin and delete. The Svelte interface exposes per-answer metrics and cached judge summaries in Results. FastAPI coordinates the work against Ollama. The main studio runs on localhost.

Release work still includes independent case review, untouched holdout evaluation, measurement on target hardware, cancellation and public deployment validation. Use the [README](../README.md) for the active workflow. The original strategy below records the earlier paid-provider and Streamlit design.

## Historical v2.1 baseline

**Version:** 2.1 (normative implementation contract)  
**Prepared:** November 6, 2026  
**Status:** Requirements ready for implementation; code, benchmark outcomes, and market adoption are NOT yet validated  
**Role in portfolio:** Project #2, complements the confirmed Hospital Ops Copilot  
**Product:** Outcome-based AI Model Evaluation, Cost Intelligence, and ROI Decision Support

> **Plain-English pitch:** ModelROI helps a product manager or engineer evaluate multiple AI models on the same realistic business tasks. It shows which model gets the most tasks right, how quickly it responds, what the tests actually cost, and which model fits the user's quality and budget requirements. It generates a report that a business manager can understand and a developer can reproduce.

> **Golden rule:** The application measures actual model outputs, token usage and task success. **Python computes the costs and recommendations. Models produce answers to test; they do not decide their own scores or invent prices.** Optional LLM-as-a-judge is secondary to executable checks and reviewed labels.

---

## v2.1 CHANGELOG AND AUTHORITY

**Date:** November 6, 2026. This is a targeted upgrade preserving the original users, positioning, interfaces, and core stack.

1. Made Wilson 95% intervals and paired McNemar comparisons mandatory. Replaced unsupported “winner/tie” language with an explicit qualified/provisional/inconclusive decision policy.
2. Defined atomic **pre-dispatch budget reservation** for concurrent calls and retry attempts; clarified the difference between internal cap and actual invoiced spend.
3. Added grading rules for free-text Hospital Ops explanations: numerical evidence subsets, verified citations, refusals, and human review of narrative meaning.
4. Fixed sampling, repeated-runs guidance, p95 low-n warning, pricing/catalog provenance and owner-only paid execution.
5. Clarified M0–M4 plus a minimum **M6 public launch** as the required product; **M5 security extension** and advanced integrations are optional. Set a single Docker Compose deployment.

**Authority order:** Sections **4, 5, 6, 9, 10, 11 and 18** override examples and background prose when there is a conflict. Prices, models, measured outcomes and customer demand are external variables to verify at execution; do not fabricate them.

---

# 1. EXECUTIVE SUMMARY FOR NONTECHNICAL READERS

## 1.1 The problem
A team may use AI to extract information from invoices, answer support questions, summarize policies, or automate work. Some models are accurate but expensive; others are fast and cheap but make more mistakes. Choosing based on published leaderboard scores alone can be misleading because the real goal is **successful work at an acceptable cost and speed**.

## 1.2 The specific product opportunity
An **easy-to-use decision lab for small AI teams** to run controlled, business-specific tests and produce auditable model-selection decisions. Existing platforms such as Langfuse, LangSmith, and AI gateways already offer many related capabilities. We are testing whether an unusually simple **cost per successful business task** workflow offers enough additional convenience or better decision support. Competition is strong; this is a product hypothesis, not an established market gap.

## 1.3 Who might use it
- AI product manager choosing a model for a specific feature and explaining the tradeoff to leadership.
- Startup engineer testing whether a cheaper model meets a required accuracy threshold.
- Consultant comparing potential vendor solutions for a client.
- Student/researcher creating reproducible task-specific benchmarking studies.

## 1.4 Examples of natural questions it answers
- "Which model meets at least 90% structured extraction accuracy and costs the least?"
- "What is the real cost per successful task after retries?"
- "Does the smaller model still meet our latency target?"
- "How many successes and failures are there in each category?"
- "What changes if we process 100,000 cases monthly?"

## 1.5 What MVP users should achieve
1. Select or import a **labeled task dataset**.
2. Pick two or three models and configure prompts and model parameters.
3. Set a maximum API budget before executing any paid run.
4. Run the exact same tasks through each model, logging failures and latency.
5. View **actual measured** quality, total spend, cost per successful task, p50/p95 latency and breakdown by task type.
6. Enter minimum quality, maximum p95 latency and maximum budget to obtain a rule-based, evidence-backed recommendation.
7. Export an evaluation report with dataset version, model IDs, pricing snapshot, scores, caveats and reproducibility instructions.

---

# 2. MARKET AND CUSTOMER VALIDATION

## 2.1 Why the problem is real
The 2026 FinOps Foundation survey reports that 98% of its 1,192 respondents manage some AI spending. **This describes a sample of FinOps practitioners, not 98% of all businesses**, and does not demonstrate willingness to pay for ModelROI. AI teams need to manage quality and variable spend; the unmet need for our particular workflow is still unproven.

**Grounding:** https://data.finops.org/ and https://www.linuxfoundation.org/press/state-of-finops-survey-ai-value-and-skills-top-priorities-as-finops-matures-across-technology-value-98-manage-ai-90-saas-64-licensing-48-data-center-1

## 2.2 Existing alternatives (validate before pitching)
- Langfuse: traces, offline/online evals, metrics, experiments. https://langfuse.com/docs/evaluation/overview
- Promptfoo: evaluation/test framework. https://www.promptfoo.dev/
- LangSmith: evaluation and observability. https://docs.smith.langchain.com/
- AI gateways such as LiteLLM offer cost and routing controls. https://docs.litellm.ai/

**Positioning:** Not another generic prompt playground or AI gateway. ModelROI begins with a user's business task, quality criterion, real-cost measurement, and a decision report. It is deliberately narrower than enterprise observability suites.

## 2.3 Customer interviews before polishing (8 people)
Target 3 startup engineers, 3 AI product managers and 2 AI/IT consultants. Ask:
1. Which AI workloads are you deploying or evaluating?
2. How do you choose a model today? Show your latest comparison if nonconfidential.
3. What are your quality, latency, cost and security thresholds?
4. How long does a normal evaluation take? Which part is tedious?
5. What happens when provider models or prices change?
6. What would you want in a one-page approval memo?
7. Would you use an external tool with a toy/nonconfidential dataset? What would stop you?
8. Would you pilot an open-source version? What would make you pay?

**Proposed validation gates (not measured results):** 5/8 cite repeated difficulty in evaluating models; 4/5 usability testers can run a controlled comparison unassisted; 3 testers can explain the recommendation and reproduce the numbers; 2 want to try it again on a different dataset. Revisit target persona if missed.

---

# 3. SCOPE: ESSENTIAL, OPTIONAL, AND EXCLUDED

## 3.1 Minimum viable product (MVP)
**Required features:**
- CSV/JSONL task-dataset import with schema check; sample files ship in repo.
- Two real model providers, plus a **mock provider** for tests and no-cost demo; optional third real provider.
- Provider/model ID and prompt-version selection; identical evaluation examples and grading rules across models.
- Rule-based graders for structured extraction, multiple choice/classification and numeric or JSON constraints.
- Timeouts, retries, transient error codes, run budget, concurrency limit and cancellation control.
- Actual provider-reported token usage where available, with an explicit estimation/unavailable status otherwise.
- Input/output/total dollar cost using a **versioned price catalog** with effective date and pricing caveats.
- Per-case success/failure, error type, elapsed time, tokens, actual/estimated cost, and provenance.
- Dashboard showing task success rate, total cost, cost per success, p50/p95 latency, failure counts.
- Rule-based model recommendation with user-set quality/latency/budget requirements and transparent reasons.
- Downloadable JSON/CSV results and a concise Markdown/HTML recommendation report.
- 50 manually reviewed evaluation cases across three task classes, **Wilson intervals, paired model comparisons**, and an uncertainty-aware report.

## 3.2 Optional improvements after MVP
- Controlled prompt-injection/unsafe tool-call simulations (AgentShield module) using no real destructive tools.
- A second prompt per model for prompt-engineering sensitivity checks.
- Optional **bootstrap** uncertainty for cost per successful task and nonbinary task scores; **Wilson 95% success intervals and paired model tests are mandatory in M3**.
- Optional human review queue and calibrated LLM judge for subjective outputs.
- Dedicated plugin/adapter for Hospital Ops Copilot evaluation cases.
- Scheduled regression checks with a carefully limited budget and explicit enablement.
- Multiple users/team workspaces and RBAC after demonstrated demand.

## 3.3 Strict exclusions from MVP
- No claim of universal "best AI model". Rankings are only valid for the tested tasks and settings.
- No real-time global model price crawler; pricing requires documented manual/automated updates and review.
- No automatic production model switching, purchasing, deployments or customer system updates.
- No open public endpoint that accepts arbitrary people's provider API keys.
- No unlicensed proprietary test data, confidential customer transcripts or patient information.
- No unbounded run budgets or unlimited provider calls.
- No claim that an LLM grader is infallible or that passing security tests certifies safety.

---

# 4. TECHNICAL ARCHITECTURE

```text
User chooses task dataset, models, requirements, and run budget
                        |
                        v
             Streamlit UI / FastAPI
                        |
       +----------------+-----------------+
       |                                  |
       v                                  v
  Dataset validator                 Run orchestrator
  + label schema                 + provider adapters
       |                         + timeouts / retry rules
       |                         + token/cost capture
       |                         + max spend / concurrency
       |                                  |
       +----------------+-----------------+
                        |
                        v
            DuckDB run/result records
                        |
             Deterministic graders
                        |
              Metrics + optimizer
                        |
         Decision dashboard + export
                        |
            (Optional) Hospital Ops
              public eval adapter
```

**One codebase, not a microservice fleet.** APIs are typed. Streamlit handles UI; FastAPI exposes functionality; DuckDB records immutable evaluations; Pydantic validates data; Pandas computes summaries; Pytest validates everything; GitHub Actions tests each change.

## 4.1 Recommended stack
| Layer | Choice | Reason |
|---|---|---|
| Language | Python 3.12+ | Widely understood, efficient for prototyping |
| UI | Streamlit | Rapid dashboards and interactive comparison |
| API | FastAPI + Pydantic | Typed interfaces; reusable integration point |
| Storage | DuckDB + local files | Simple repeatable evaluation history |
| Model calls | Small provider adapter layer using official SDKs | Stable interface even as APIs change |
| Tests | Pytest + offline mocks | Reliable tests without paid APIs |
| Validation | JSON Schema, deterministic graders | Auditable pass/fail |
| Charts | Plotly or Streamlit built-ins | Clear business visuals |
| CI | GitHub Actions | Evidence of professional engineering |
| Container | Docker | One-command reproducibility |

### 4.2 Provider adapter contract
Every real or mock provider implements the same interface:

```python
class ModelAdapter:
    async def generate(self, model_id: str, messages: list, settings: dict) -> dict:
        """Return output, provider model ID, token usage, runtime, error info.
        No credentials or secrets appear in the returned record."""
```

Return structure (illustrative schema, not measured values):
```json
{
  "provider": "example-provider",
  "model_id": "exact-model-version-at-run-time",
  "output_text": "example result",
  "input_tokens": 0,
  "output_tokens": 0,
  "cached_input_tokens": 0,
  "usage_status": "provider_reported",
  "latency_ms": 0,
  "status": "success",
  "error_code": null
}
```

Each provider adapter must translate vendor-specific token/usage fields. **Unknown token usage stays null or marked estimated**, never converted into a false zero-cost result.

### 4.3 Run-state machine
`CREATED -> VALIDATED -> APPROVED_BUDGET -> RUNNING -> COMPLETED / PARTIAL / FAILED / CANCELLED`
- Each test case has stable `case_id` and never silently changes during a run.
- Capture model ID/version, prompt hash/version, dataset version, model settings, time, pricing snapshot, request IDs and failure category.
- A failed API request is not dropped from totals. Capture its known monetary costs where available, or label the amount unknown.
- Retry only on configured transient failure types, with exponential backoff and a maximum total cost/time budget.
- Cancel stops new calls; in-flight calls may still incur cost. Warn the user.
- Do not compare models as equivalent if prompt/tool affordances differ substantially without disclosing that limitation.

---

# 5. EVALUATION DATA, GROUND TRUTH AND GRADING (NORMATIVE)

## 5.1 Fixed and holdout data

Ship **50 original/reviewed cases** with stable IDs, dataset version, provenance, task type, reference answers, grader version, and `split`:
- `structured_extraction`: **20** fictional invoices/purchase orders; expected JSON fields and missing-value rules.
- `hospital_finance_qa`: **20** questions based on independently verified Hospital Ops finance fixtures and typed `EvidencePacket` values. Use a small public/synthetic mock if Hospital Ops is not yet built, and label that limitation.
- `instruction_following_classification`: **10** verified categorical/constraint cases, optionally selected from openly licensed IFEval with attribution.

A **separate holdout set of ≥10 previously unused cases** is for final checks; it is not tuned against and is not pooled with the initial 50 when reporting the primary denominator. For model pair comparisons, use exactly the **same case IDs**, fact packets and graders. Log excluded cases and why; timeouts/refusals count as failures unless a scenario-specific rubric says the refusal is correct.

**Example JSONL row:**
```json
{"case_id":"invoice-001","task_type":"structured_extraction","input":"Synthetic invoice INV-01 with amount $42.50","expected":{"invoice_id":"INV-01","amount":"42.50"},"grader":"json_fields_exact","critical_fields":["invoice_id","amount"],"source_license":"original_synthetic","split":"dev","dataset_version":"v1"}
```

## 5.2 Deterministic grading rules

| Grader | Acceptance rule | Failure examples |
|---|---|---|
| `json_fields_exact` | Required keys/types, canonical dates, fixed-decimal amounts and explicit normalization match reviewed gold values | Missing critical field, extra unsupported required field, wrong amount |
| `classification_exact` | Predicted normalized label in the predeclared allowed-label set | Invalid category, unapproved synonym |
| `instruction_checks` | Named executable constraints pass | Prohibited word, invalid structure |
| `numeric_facts_subset` | Every **material** financial number in answer corresponds to an allowed typed `fact_id` from the packet after normalizing currency, percentages, rounding and units | New unsupported margin, fabricated percentage, changed period |
| `citation_grounding` | Every cited `source_id` exists in the same evidence packet; named metric/period has the relevant cited field and source report | Invented URL, missing CCN or wrong fiscal period |
| `valid_refusal` | Out-of-scope live/clinical/PHI prompt returns the specified limitation and no unsupported factual claim | Pretend live capacity figure |

**For hospital free-text Q&A:** Use the actual packet with approved numeric fact IDs, source IDs, and approved rendered figures. Validate that any material numeric claim is from the packet; exempt only explicitly classified nonfinancial numeral contexts (report identifiers, dates, model version strings) using **typed field classification**, not a blanket regex pass. This validates numeric support; it cannot establish that a free-form narrative is clinically/financially sensible. Keep a **human review** rubric for logical/causal claims and source-support quality, with disagreements recorded. If claims cannot be parsed/verified, fail the automated grounding check or mark for review; **never silently pass**. Citation test requires source presence *and* the correct backing field/period, not merely any citation. The LLM cannot be the sole judge of its own output.

**Grader invariants:** Frozen labels are never recomputed from the candidate model's answers or the very code being tested. Save scorer version, exact mismatch diagnostics, and reviewer adjudications.

## 5.3 Paired datasets and repeat policy

At least **one full controlled run per selected model on all 50 cases** for the initial MVP. Keep `temperature=0` when the provider supports it; otherwise record the actual setting and that determinism is not assured. Record all sampling options, system/user prompts, input formatting, tool availability, seed if supported, provider-returned model ID/version, API region if relevant and timestamps. A one-run score is a **snapshot, not proof of reproducibility across runs**. Optional follow-up: 3 repeated runs per model for variance; report them separately, never silently mix with the single-run benchmark. Matched comparisons must have equivalent tool access, prompt instructions and token limits; disclose any unavoidable vendor differences.

## 5.4 Data privacy and licensing

No PHI, no employer-confidential inputs, and no model API keys in uploaded data. Only original synthetic or licensed benchmark content is committed. Reject executable grader code or arbitrary file paths in uploads. Describe provider retention and costs honestly before sending any user input to an external provider.

---

# 6. METRICS, STATISTICAL EVIDENCE, COST AND DECISION ENGINE (NORMATIVE)

## 6.1 Core accounting definitions

- `attempted_cases`: every scheduled evaluated case reaching first dispatch; timeouts, errors and invalid outputs count as **unsuccessful** attempts. Report separate `not_attempted` when cap prevents dispatch; never quietly remove them from run-completeness calculations.
- `successful_cases`: cases passing every mandatory task-specific checker, with manual adjudication noted where required.
- `observed_success_rate = successful_cases / attempted_cases`; also report `coverage = attempted_cases / planned_cases`. A comparison with missing planned cases is **incomplete**, not a full-run winner.
- `total_known_cost`: sum of recorded provider usage charges for all attempts and retries **plus graded-cost calls** when applicable. Track `estimated_cost`, `unknown_cost_count` and `provider_billed_verified_cost` separately. Failed calls may still cost money. Never replace missing usage with zero.
- `cost_per_success = total_known_cost / successful_cases`; zero successes => `N/A`; unknown paid costs => “incomplete estimate,” not exact unit economics.
- `cost_per_1000_attempted_tasks = total_known_cost / attempted_cases × 1000`; classify result as `estimated` unless provider invoice has been manually reconciled.
- `projected_monthly_api_cost = measured_per_attempt_cost × user_input_monthly_attempts` **only** with price/model assumptions and a scenario/uncertainty label. Exclude hosting/labor/security from “API-only” projections explicitly.
- `p50` and `p95` use **nearest-rank** sorted empirical percentiles (`rank = ceil(p×n)`), measured from client dispatch to final completion including retries/timeouts (plus optional separate per-call latency). At `n=50`, p95 is approximately the **third slowest** observation and is noisy; display `n` and the low-sample warning. If fewer than **100** completed task observations, p95 is **exploratory**, not a certified latency SLA. Show failed/censored timing records explicitly rather than dropping them without note.

## 6.2 Mandatory 95% uncertainty reporting and paired model comparison

For each model and task category, show `n`, successes, observed success proportion, and **two-sided 95% Wilson score interval** (`z=1.96`). For 18 successes in 20 trials, expect approximately **69.9%–97.2%**. CI does **not** prove future quality or independence; all inference is conditional on test-case representativeness and model settings.

For two models answering the same labeled cases, build paired binary pass/fail outcomes and count **discordances** (`A_pass/B_fail` and `A_fail/B_pass`). Use the **exact two-sided McNemar/binomial test** on discordant pairs (if discordant count = 0, report `p = 1.0`, no detected difference). Report paired case count, discordance table, p-value and **effect size (paired pass-rate difference)**. With ≥3 models apply Holm adjustment across pairwise tests; name significance threshold (`α=0.05`) and multiplicity method. `p > 0.05` is **insufficient evidence to establish a difference**, NEVER “tied” or “equivalent.” A significant result also does not guarantee superior performance on unseen real workloads.

With small data, do not claim a winner on measured accuracy solely because one model scored e.g. 45/50 versus 44/50. Explain that the observed ordering is uncertain. Bootstrap intervals for `cost_per_success` are optional and should stratify/resample paired cases if used.

## 6.3 Pricing catalog and pre-dispatch budget reservations

`config/pricing.yml` is a **versioned snapshot** with provider/model canonical IDs, effective timestamp, source URL, input/output/cached token prices, currency, reasoning/tool surcharges, usage tiers and model token constraints. Verify current official pricing and billable usage fields before every **published** real run; freeze a `pricing_snapshot_hash` with each experiment. A provider with unknown price tier, unbounded charge type, unknown maximum context/output charge, or incomplete model billing semantics is **disabled for paid runs** until bounded conservatively.

**Budget invariants (per run and per owner account):**
1. User confirms `max_budget_usd`, `max_concurrency`, maximum prompt/input tokens, `max_output_tokens`, retry limit, and an optional fixed lower global daily spend ceiling. First estimate input tokens with provider tokenizer or conservative upper bound; reject input above the supported bound.
2. Before **any** dispatch, atomically acquire a **reservation covering that case's worst-case cost for the first call plus every permitted retry and grader call**, including conservative markup for token-count uncertainty and known surcharges. Compute output cost at `max_output_tokens`. Never dispatch when `spent_recorded + reserved_open + new_reservation > run_cap` or remaining owner daily quota.
3. Make reservation updates **transactional and serialized** under concurrency (database transaction + single-writer/lock; unit-test with racing requests). One request cannot use another's reserved budget; no negative availability.
4. After each provider attempt, capture actual reported usage and reconcile the reservation. Release only the verified **unused** amount when all retries/graders for that case are concluded; if usage/cost is unknown, keep a conservative liability reservation and mark `needs_manual_reconciliation`.
5. Cancellation forbids *new* dispatches. Already in-flight requests may still be billed; disclose this before execution. Timeouts/retries only run if the remaining reserved liability covers them.
6. The cap is a **local modeled spending guard**, not a promise that a provider invoice cannot exceed it. Unexpected provider billing may require manual invoice reconciliation. If safe upper bounds cannot be established, return a user-visible “Cannot safely estimate this run” error without dispatching paid calls.

Capture all attempts with `request_id`, concurrency slot, attempt number, status, error, token counts, price version, reservation, estimated vs provider-reported and manually billed costs. **Do not claim automatic ‘billed’ reconciliation**: provider-console/invoice verification is a recorded human step.

## 6.4 Recommendation policy: evidence-aware, no AI scoring the winner

Inputs: min success requirement, max observed p95 latency, max estimated API cost per 1000 attempts/monthly budget, optional severe-error ceiling; every constraint is written into the report. For each model:

1. Require **full planned-case coverage**, adequate labels and grader completeness, known cost bounds and mandatory safety checks; otherwise `INELIGIBLE_INCOMPLETE`.
2. Show Wilson interval, counts and paired evidence for comparisons. For a **quality-certified** recommendation at required success rate `q`, require the **Wilson 95% lower bound ≥ q**; if observed pass rate ≥q but Wilson lower bound <q, flag **PROVISIONAL_INSUFFICIENT_EVIDENCE** (not a certified winner). Never automatically lower confidence requirements.
3. For an SLA-like strict latency limit, also require sufficient latency sampling and credible measure (`n ≥100` completed observations as an initial practical gate). With `n <100`, label latency evidence **PROVISIONAL** even if the observed p95 meets the limit. At least 100 observations are necessary but not sufficient to substantiate a latency SLA; repeated calls on the same cases are correlated, and deployment conditions may differ. Non-SLA exploratory runs may still show results but cannot imply certified compliance.
4. Apply disclosed budget and severe-error constraints. If `estimated` or unbounded spending is unacceptable under user requirements, return **INELIGIBLE_COST_UNKNOWN**. Out-of-range candidates are listed with reasons.
5. Among candidates passing all required *evidence gates*, pick the lowest observed cost per success, tie-break by higher observed success and then lower p50. Call this **“lowest observed cost among qualifying models on this workload”** and distinguish it from claims of statistically better model quality. Present McNemar results next to ranking.
6. If none passes, say **“No model is sufficiently evidenced to meet all selected constraints”**, with the specific missing sample or cost reason. If the user explicitly chooses **exploratory mode**, a provisional lowest-observed-cost candidate may be displayed with clear “NOT VALIDATED / INSUFFICIENT EVIDENCE” labeling; never invent statistical equivalence.

Use a basic Pareto scatter of observed cost, quality and latency without an opaque weighted score. A cost saving based on tested examples is not realized production ROI.

## 6.5 Example, hypothetical only

Model A: $4 for 100 cases and 80 successes = $0.05 per success. Model B: $6 for 100 cases and 95 successes ≈ $0.0632 per success. If a quality requirement is 90%, A fails by point estimate; B may still have a Wilson lower bound below 90%, so **neither is automatically “quality certified”**. This example is not measured evidence.

---

# 7. USER EXPERIENCE: SIX SCREENS

**Screen 1. Select workload**: choose one included sample or upload validated JSONL/CSV; show dataset size, categories and terms.

**Screen 2. Configure experiment**: choose 2-3 models, prompt version, temperature, retries, maximum spend, max concurrency; confirm the API cost cap.

**Screen 3. Run progress**: attempted/completed/failed cases, spent so far, error types, stop/cancel. No exposed secrets.

**Screen 4. Comparison dashboard**: side-by-side success rate, total spend, cost per success, latency p50/p95; category-level breakdown and Pareto view.

**Screen 5. Failure explorer**: inspect each test input, model output, expected answer, deterministic grader result, retry history, and judge disagreement if applicable.

**Screen 6. Model recommendation report**: form for business constraints, qualified candidates, selected model, price version, confidence/caveats and export to HTML/Markdown/CSV.

---

# 8. API CONTRACTS (FOR AI CODING AGENTS)

- `GET /health`: service health and schema version.
- `GET /v1/datasets`: list installed curated datasets and counts.
- `POST /v1/datasets/validate`: validate schema and summarize errors; no execution.
- `GET /v1/models`: available configured providers, model IDs, pricing status.
- `POST /v1/runs/estimate`: calculate conservative worst-case **reservation** before execution using bounded inputs, maximum output tokens, all retries/graders, surcharges and current catalog. Reject unsafe unknown prices.
- `POST /v1/runs`: owner-only/local authenticated paid execution with atomic budget reservations; **not available to public demo users**.
- `GET /v1/runs/{run_id}`: status and progress.
- `POST /v1/runs/{run_id}/cancel`: stop new calls.
- `GET /v1/runs/{run_id}/results`: paginated per-case results.
- `POST /v1/recommendations`: evaluate constraints against a saved completed run; returns reasons and caveats.
- `GET /v1/reports/{run_id}`: download audit report with model IDs, prompt and pricing versions.

**Sample recommendation request (fictional constraints):**
```json
{
  "run_id": "sample-run-id",
  "required_success_rate": 0.90,
  "max_p95_latency_ms": 3000,
  "max_cost_per_1000_attempts_usd": 3.00,
  "monthly_attempts": 100000
}
```
Return `eligible`, `ineligible_reasons`, `winner_model_id`, `metrics`, `caveats`, and `report_version`. Do not allow user-supplied arbitrary Python, shell or SQL expressions to execute.

---

# 9. CANONICAL REPOSITORY LAYOUT AND DEPLOYMENT

Use the single `app/` Python package below. Hosting is **one Docker Compose deployment**, with two containers (FastAPI API + Streamlit UI) on a host that supports Docker; the UI addresses `http://api:8000` internally. The public UI serves **offline mock and frozen historical benchmark results only**; all real paid runs require local use or authenticated owner-only access, with server-side provider credentials and hard UI disablement for public users. Store run/ledger state in an owner-only persistent volume (not public Git).

```text
modelroi-ai/
  README.md  LICENSE  .env.example  .gitignore  pyproject.toml
  Dockerfile  docker-compose.yml  Makefile  .github/workflows/ci.yml
  config/{pricing.yml,models.example.yml}
  app/
    __init__.py
    api/main.py
    ui/Home.py  ui/pages/
    datasets/validate.py
    providers/{base.py,mock_adapter.py,openai_adapter.py,second_provider_adapter.py}
    execution/{runner.py,budget.py,retry.py}
    graders/{json_exact.py,classification.py,instruction_checks.py,numeric_facts_subset.py,citation_grounding.py,valid_refusal.py}
    metrics/{aggregate.py,pricing.py,decision.py,uncertainty.py,paired_tests.py}
    storage/{models.py,ledger.py}
    reports/export.py
  datasets/v1/{structured_extraction.jsonl,hospital_public_fixtures.jsonl,instruction_following.jsonl}
  evals/holdout/README.md
  tests/{test_graders.py,test_budget_races.py,test_stats.py,test_decisions.py,test_api.py}
  docs/{architecture.md,evaluation_methodology.md,pricing_and_limitations.md,product_requirements.md,market_validation.md,security.md,decision_log.md}
  examples/{mock_run.json,measured_run.example_schema.json}
```

Startup tests: `pip install -e '.[dev]'`, `pytest -q`, `uvicorn app.api.main:app --reload`, `streamlit run app/ui/Home.py`, `docker compose up --build`. Public demo must use a **labeled recorded result** or mock mode without provider credentials; never accidentally invoke paid APIs from page load or test CI.

---

# 10. DETAILED BUILD SEQUENCE AND DEFINITION OF DONE

## M0: Repo foundation and mock demonstration
**Tasks:** initialize Git repo, Python environment, type-checked schemas, offline mock adapter, minimal UI, FastAPI `/health`, Docker, Pytest, GitHub Actions.

**Demonstration:** `pytest -q` passes offline and a mock evaluation of five cases runs end to end without paid APIs.

**Acceptance:** documented setup works on a clean machine; tests and lint green; no credentials in repo; API health check and mock dashboard visible.

## M1: Datasets and grading
**Tasks:** write dataset schemas, original synthetic tests, curated gold labels; implement deterministic JSON/classification/numeric/constraint graders; prepare 50 tasks and held-out cases.

**Demonstration:** deliberately correct examples pass, deliberately incorrect examples fail, malformed records produce understandable errors.

**Acceptance:** all 50 cases have versioned gold criteria, case IDs and provenance; no hidden state affecting grades; tests include missing/invalid values and ambiguous outputs.

## M2: Actual provider integration and safety budget
**Tasks:** add first real API adapter then second; support environment-only credentials, provider-specific usage mapping, token prices and versions, retries/timeouts, total cost cap, status machine, cancellation; persist run records.

**Demonstration:** complete a minimal authorized run of 5 cases x 2 models under an intentionally low dollar cap and show actual usage when provider reports it.

**Acceptance:** the **atomic pre-dispatch reservation algorithm in Section 6.3** passes concurrent dispatch/retry/cancel/unknown-pricing race tests, including worst-case tokens and retries; paid runs are owner-only; every attempt is recorded and unknown charges are never zeroed out. No request is sent without a valid reservation.

## M3: Metrics and rules engine
**Tasks:** implement per-model and per-case measurements; p50/p95 with sample-count warning, total cost and cost/success; **mandatory Wilson intervals and exact paired McNemar**; Holm-adjusted comparisons when needed; conservative constraint filtering and no-certified-model result.

**Demonstration:** the program reproduces metrics from a small independently hand-calculated fixture.

**Acceptance:** 30+ metric/decision edge-case tests pass, including all-failed, unknown cost, quota exhausted, underpowered quality/latency, statistically inconclusive models, McNemar discordances, retries and missing labels. Check Wilson 18/20 ≈ 69.9%–97.2%.

## M4: Dashboard, failure explorer, exports
**Tasks:** four Streamlit pages and reports; clear source labels; filter by task, model and failure; show a **qualified recommendation only when the mandatory evidence gates pass**, else an explicit provisional/inconclusive decision with reasons.

**Demonstration:** a nontechnical user can compare two models, see failed examples, apply quality/cost requirements and export a one-page business case.

**Acceptance:** dashboard totals agree exactly with CLI/API results; JSON/CSV export equals run records; no broken links; accessible labels and readable figures.

## M5: OPTIONAL evaluation and security extension (AgentShield-lite)
**Tasks:** 10-20 controlled adversarial tasks for prompt injection, role confusion, malicious instructions inside retrieved sample text, hallucinated citations, unapproved tool calls in mock sandbox. Use test doubles, never real external destructive actions.

**Demonstration:** display a security test category and identify failures with reproducible expected behavior. Distinguish model response behavior from actual system control enforcement.

**Acceptance:** no real privileged action is triggered by tests; security cases are labeled and reviewed; the README states results do **not** certify production security.

## M6: REQUIRED public release; optional extended integration and user validation
**Required tasks:** support one explicitly authorized real benchmark (fixed model IDs, valid price snapshots and reproducible results), deploy an **offline public** demo with stored, truthfully labeled results, add README/case study, release tag and one-command Docker setup. A complete M6 product release requires an actually measured two-provider benchmark; if authorization or funding is unavailable, publish a clearly labeled **mock-only preview** and mark full M6 incomplete. **Optional parallel tasks:** expand Hospital Ops adapter to 10–20 cases, conduct up to five usability tests and eight interviews. Research participation does **not** block the GitHub release.

**Acceptance:** a new user can run local mock mode at zero provider cost, inspect a real recorded benchmark with date/models/case IDs and pricing snapshot hash; CI and release checks pass. If paid authorization is unavailable, the public preview may launch but **must not be marked as full MVP complete**. The public UI cannot start paid runs. Do not claim a completed real-provider comparison until it actually ran.

---

# 11. RELEASE QUALITY GATES

| Gate | Objective | How measured |
|---|---|---|
| Reproducible grading | All graders, including numeric-grounding and citation checks, agree with independently reviewed fixtures | `pytest` plus audit fixtures |
| Labeled test suite | At least 50 vetted cases across 3 classes | Dataset validation job |
| Robust accounting | All known paid calls counted, unknown costs explicitly marked | Provider mock fault-injection tests |
| Safe spending | Atomic worst-case reservation before concurrent requests, including retries | Racing-request/unknown-price/cancellation fault tests |
| Trustworthy decisions | Wilson intervals, paired McNemar, cautious quality/latency constraints, never falsely certified | Statistical fixtures, underpowered/no-eligible tests |
| Traceability | Every result includes run, case, prompt, model, dataset and pricing versions | Schema validation |
| Honest reporting | No invented model performance / realized ROI | README review |
| Accessible handoff | Offline `make demo` or equivalent works without API keys | Fresh-install smoke test |
| CI and secrets | Tests run in PR CI, keys excluded | GitHub Actions and secret scanner |

**A 50-case set is too small to certify near-threshold reliability for many workloads.** Show 95% Wilson intervals, paired McNemar outcomes, a p95 low-sample warning, and provisional/inconclusive status. Any optional subjective judge must first be calibrated against independently reviewed examples; it never overrules deterministic safety/citation checks.

---

# 12. SECURITY AND ETHICS

- Read provider key from server-side environment or approved secrets manager only. Never log keys, send them to UI state, or commit them.
- For the public demo, disable paid evaluation execution by default; use cached, correctly labeled example runs. Enable live runs only for authenticated/authorized owner or in local mode.
- Validate uploads, file size, JSONL schema, MIME, and token estimates; limit disk, CPU, concurrent jobs, API requests and per-run spend.
- Avoid logging prompts/results by default if they could include confidential user information; offer clear retention/deletion controls before accepting user uploads.
- Never load arbitrary Python grader code from public uploads; predefined allowlisted evaluators only.
- Respect provider policies and data retention rules when sending prompts to their APIs.
- Treat prompt injection within candidate model output as **data**, not instructions to the orchestrator.
- Security tests happen in a sandbox with fake tools. The benchmark alone does not establish regulatory compliance or safe production deployment.
- Review licenses and attribution for any outside benchmarks or code.

---

# 13. PRODUCT VALUE, PRICING HYPOTHESES AND BUSINESS GO/NO-GO

**First user segment:** product managers and engineers in small teams evaluating 2-5 models for one business use case.

**Measurable user outcomes:** minutes to create a comparison, proportion of correct model-selection explanations, reproducibility of result, repeat usage on a second workload, reports shared internally, user's stated confidence in the decision.

**Not measured until users actually test:** revenue, customer adoption, conversion, ROI, realized cost savings, model-switching outcomes.

**Commercial experiment:** ask interviewees to use the free local version, then test their reaction to a paid hosted feature such as persistent team reports, scheduled regression checks or collaboration. Do not build subscription billing based only on survey stats. The open-source core should remain useful without a subscription.

**Kill/pivot signal:** if target users prefer their existing Langfuse/Promptfoo setup and cannot identify a painful decision-reporting gap after five usability sessions, narrow to an educational evaluation lab or a lightweight report generation integration.

---

# 14. CONNECTING PROJECT #2 TO PROJECT #1

The portfolio should show that **Hospital Ops Copilot is a real application** and **ModelROI is the independent tool that measures the AI components powering it.**

## 14.1 Shared evaluation contract
Hospital Ops exports public benchmark QA cases with `case_id`, user `input`, `expected` tool or answer evidence, `task_type`, dataset version and risk level. ModelROI imports them through a documented local JSONL adapter or read-only API.

**Do not include:** private hospital/customer records, sensitive user prompts, API keys or live write privileges. Do not couple ModelROI to an internal database schema that could expose unnecessary information.

## 14.2 Two complementary comparisons
1. **Full system test:** Compare Hospital Ops' deterministic tool-grounded answers with ground truth; any model answer that invents a number fails.
2. **Model-choice test:** Hold retrieved facts constant and test alternative LLMs' explanations, citation discipline, latency and inference cost.

This distinction matters: a better model does not fix incorrect hospital source data or wrong cohort calculations.

## 14.3 Shared publication deliverables
- Diagram showing Hospital Ops -> labeled evaluation cases -> ModelROI -> measured decision report.
- A single example of a model recommendation with **actual, timestamped results** (do not fabricate figures).
- Links in each README to the other repo, but keep both independently installable.
- One joint video demonstrating a hospital benchmark, then the model evaluation that verifies its AI explanations.

---

# 15. READY-TO-USE PROMPT FOR AN AI CODING AGENT

Copy this prompt to Claude, Codex, or another coding assistant and attach **this entire plan**:

> You are the engineering lead building ModelROI AI. Treat the attached document as the source of truth. Begin with M0 only. Before code, inspect the repository, summarize the acceptance criteria for M0, and create a small implementation plan. Implement the minimal files needed for M0, run tests and show the real output. Do not claim success if tests did not run. Do not build M1-M6 until I approve or request the next milestone. Default to offline mock mode, no hardcoded provider keys and no paid API calls without my authorization and a budget cap. Keep Python code modular, documented, and accessible to a beginner. Use a single Streamlit + FastAPI + DuckDB stack. Finish with: modified files, commands executed, observed results, open issues, and the next milestone.

---

# 16. GLOSSARY

- **LLM:** Large language model, the AI system answering a test prompt.
- **Evaluation / eval:** Repeatable test that checks whether AI output meets defined criteria.
- **Ground truth:** Correct expected output or rubric, reviewed before model testing.
- **API:** Standard method for software to communicate with another software service.
- **Token:** Unit in which many model providers measure text usage and price.
- **Latency:** Time from sending a request until a response is received.
- **p95:** nearest-rank 95th-percentile latency, including stated retry behavior; at 50 cases it is noisy and must carry a low-n warning.
- **ROI:** Return on investment; genuine financial ROI requires costs and realized benefits, not just inference spend.
- **Cost per success:** All observed run cost divided by successful tasks, when costs and labels are complete.
- **JSONL:** Text format storing one structured JSON object per line.
- **CI:** Automated testing of changes through continuous integration.
- **Pricing snapshot:** Dated record of provider pricing and tiers used to calculate estimated costs.
- **Prompt injection:** Attempts to make an AI system ignore its instructions through untrusted input.

---

# 17. PRIMARY REFERENCES

- 2026 State of FinOps: https://data.finops.org/
- OpenAI evaluation best practices: https://developers.openai.com/api/docs/guides/evaluation-best-practices
- OpenAI current API prices: https://developers.openai.com/api/docs/pricing
- Google IFEval, Apache-2.0: https://huggingface.co/datasets/google/IFEval
- Langfuse evaluation docs and competing product capability: https://langfuse.com/docs/evaluation/overview
- Hospital Ops project plan in this package: `Hospital_Ops_Copilot_Final_Build_Plan.md`

---

# 18. v2.1 EXECUTABLE ACCEPTANCE EXAMPLES

**All example outcomes are synthetic expectations, not measured provider results.** Every item should be expressed as an automated regression or clearly marked manual acceptance check.

| Test ID | Input | Expected result |
|---|---|---|
| M-T01 | 18 passes among 20 reviewed independent binary outcomes | Wilson 95% interval approximately **69.9%–97.2%** |
| M-T02 | Same seven discordant cases: A-only wins=6, B-only wins=1 | Exact two-sided McNemar/binomial `p = 0.125`; cannot establish a difference at 0.05 |
| M-T03 | Models score 45/50 and 44/50 on identical cases | Report paired discordances/CI; do **not** assert quality superiority from point estimates alone |
| M-T04 | Quality threshold 90%, candidate observed 18/20=90% | Wilson lower bound < 90%; status `PROVISIONAL_INSUFFICIENT_EVIDENCE`, not certified |
| M-T05 | 50 completed task latencies | Show nearest-rank p95 (48th sorted latency), sample count 50 and low-n warning |
| M-T06 | Concurrent A and B reserve $0.60 each against cap $1.00 | Transactional budget permits **at most one** reservation; second call is not dispatched |
| M-T07 | Call reserves first attempt + 2 retries + grader; timeout occurs | Retry may proceed only under existing reservation; known spend and remaining liability reconcile |
| M-T08 | Pricing tier unavailable or provider charges unbounded tool fee | Paid run rejected **before dispatch**, with a reason; no fake zero-cost treatment |
| M-T09 | Cancel during two in-flight calls | No new calls dispatched; in-flight liabilities retained and logged |
| M-T10 | Hospital answer includes `3.42%` from approved `0.0342` fact | `numeric_facts_subset` passes after typed normalization; citation must point to corresponding source field/period |
| M-T11 | Hospital answer invents `7.9%`, missing support, or cites wrong period | Numerical-grounding or citation grader fails; invalid model output recorded |
| M-T12 | Public anonymous user presses “Run paid benchmark” | UI and API prohibit paid run; offline/mock result available instead |
| M-T13 | A model costs less per attempt but violates quality threshold | Excluded from quality-qualified recommendation; show tradeoff |
| M-T14 | Provider invoice has not been manually checked | Label `provider-billed cost: not reconciled`, not `actual billed = estimated` |

**Full-MVP cut line:** M0–M4 and minimal M6 with **real dated, authorized two-provider measured evidence**. M5 AgentShield security suite and advanced Hospital Ops integration are optional. If no paid run is authorized, the repo can still publish a labeled mock-only preview; it does not satisfy the full-product acceptance gate. User interviews and usability tests do **not** block technical release.
