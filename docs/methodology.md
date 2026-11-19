# Methodology

How ModelROI produces each number on screen, and what those numbers do and do not show.

## Quality grades

Prompt and benchmark grades use five dimensions: correctness, relevance, completeness, instruction
following and faithfulness (support from provided evidence). The overall v2 grade is the arithmetic
mean of the applicable dimensions. Missing source evidence can yield N/A for faithfulness.

Results keep the judge's identity, rubric version, scores and overall comment. Historical holistic
grades keep their original meaning.

For a custom grading target, select **Reference answer** in the composer before sending a question.
Only the judge receives the reference. Expand an answer's **Metrics** to inspect the saved
reference.

## Benchmark checks

Benchmarks check exact expected values and JSON key and type structure, separately from the judge.
Exact JSON checks preserve types: numeric `1` does not equal boolean `true`. Exceptions count as
failed cases, and truncated outputs fail grading. An answer that is exactly one Markdown code block
(for example ```` ```json ... ``` ````) is unwrapped before checking and marked `json_fenced` in the
saved result; any other text around the JSON still fails as invalid.

| Metric | Definition |
|---|---|
| Task success | Share of cases whose output matched the expected answer |
| 95% Wilson interval | Uncertainty on the success rate at the sample size used |
| Schema compliance | Share of outputs with the expected JSON keys and types |
| Extraction field micro-F1 | Correctly extracted key/value pairs, pooled over predicted and expected fields |
| Request error rate | Failed executions; a valid but wrong answer can fail the task even when the request succeeded |
| p50 and p95 | Nearest-rank elapsed attempt latency, including failed attempts |
| Decode throughput | Ollama's token generation rate, from its reported generation duration |
| Token counts | Input and output tokens as reported by the provider |
| Paired comparison | Exact test on cases only one model passed, with Holm adjustment across pairs |

## Ranking

Before a matched benchmark, set the **Ranking thresholds**. Defaults are 80% task success and 95%
schema compliance; the optional p95 limit is in seconds. A model that misses any threshold is listed
with the reason and is not ranked.

Eligible models receive a weighted score for that run:

| Component | Weight | Scaling |
|---|---|---|
| Task success | 50 | Measured rate |
| p95 speed | 20 | Inverse min-max among eligible models |
| Provider fees per success | 20 | Inverse min-max among eligible models |
| Request reliability | 10 | 1 minus the request error rate |

Equal values tie. If any model lacks cost data, the cost weight is removed for the whole
comparison. Local provider fees exclude hardware and electricity.

## Conversation context

Each model uses its own recent turns as limited conversation context. User messages and references
do not train model weights. Budgets for standard, extended and hosted long context are described in
[setup.md](setup.md#longer-follow-up-context-on-macos).

## Run records

The local runner records the model digest when Ollama supplies it, the dataset SHA-256, settings,
token counts, UTC start time and per-case elapsed time. Completed prompt turns and benchmarks are
stored under `~/.modelroi/runs`, including submitted excerpts.

SQLite stores saved turns, report details, chat metadata and benchmark measurements in
transactions. History lists read indexed summaries without loading full answers. DuckDB powers
**History → Analyze saved benchmarks**, calculating pooled pass counts, mean judge grades and median
latency across saved runs. See
[migration and backup instructions](setup.md#local-storage-and-migration).

## Limits

- These are exploratory relative scores on draft cases. Human-reviewed references, repeated trials
  and independent validation are still needed for release decisions.
- No comparative model winner is claimed.
- Latency is machine-specific and exploratory with fewer than 100 observations.
- Zero provider API fees do not imply zero electricity or hardware cost.
- Hospital cases are synthetic arithmetic examples, not independently verified CMS facts. The
  current graders do not implement the entire financial grounding specification.
- Source-grounding grades are judge assessments, not measured hallucination rates.
- Time-to-first-token requires token streaming, repeated-run consistency needs repeated trials, and
  safety or tool-use pass rates need labeled tasks and instrumentation. The dashboard does not
  estimate those quantities from a single answer.
- Simulated provider tests are not evidence of actual model performance.
