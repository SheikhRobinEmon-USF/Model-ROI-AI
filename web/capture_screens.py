"""Regenerate the README screenshots in docs/images.

Every API response is replaced with the SAMPLE DATA below, so the pictures show the
interface, not measured model performance. Start the studio API first:

    MODELROI_ENABLE_LOCAL=true python -m uvicorn modelroi.api.main:app --port 8598
    python web/capture_screens.py
"""
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = os.getenv("MODELROI_URL", "http://127.0.0.1:8598/")
OUT = Path(__file__).resolve().parents[1] / "docs" / "images"
now = datetime.now(timezone.utc)

MODELS = [dict(id="qwen3:4b", name="Qwen3 4B", installed=True), dict(id="gemma4:e4b", name="Gemma 4 E4B", installed=True)]
PROMPT = "A clinic's revenue grew 12% to $4.2M while costs rose 9% to $3.1M. What happened to its operating margin?"


def judge(score, reason):
    return dict(score=score, reason=reason, scope="Answer quality", criteria={}, model="gpt-oss:20b", rubric_version="quality-v2",
                dimensions=dict(correctness=score, relevance=min(10, score + 1), completeness=score,
                                instruction_following=min(10, score + 1), faithfulness=None))


def answer(model, score, ms, output, reason):
    return dict(requested_model=model, status="Answered", output=output, latency_ms=ms, input_tokens=212,
                output_tokens=340, decode_tokens_per_second=41.3, judge=judge(score, reason))


CHAT = dict(
    run_id="11111111-1111-4111-8111-111111111111", started_at=now.isoformat(), model_id="Qwen3 4B / Gemma 4 E4B",
    evidence_type="custom_prompt", prompt=PROMPT,
    answers=[
        answer("qwen3:4b", 6.5, 4210, "The margin went up because revenue grew more than costs. It is now roughly 26%.",
               "Reaches the right direction and final margin but omits the starting margin and the size of the change."),
        answer("gemma4:e4b", 9, 2890,
               "Operating margin before: revenue was $3.75M and costs $2.844M, so margin was 24.2%.\n\n"
               "After: ($4.2M − $3.1M) / $4.2M = 26.2%.\n\n"
               "The margin improved by about 2.0 percentage points because revenue grew faster than costs.",
               "Computes both margins correctly and states the change in percentage points; the explanation is concise."),
    ],
    comparison_summary=dict(model="gpt-oss:20b", text="Gemma 4 E4B earned the higher grade: it showed both margins and the change, "
                            "and answered faster. Qwen3 4B reached the right direction but skipped the starting margin."))


def run(model, passed, p50, p95, grade):
    rows = [dict(case_id=f"math-00{i + 1}", input="A ward has 28 beds at 86% occupancy. How many more patients fill it to 95%?",
                 expected={"answer": 3}, passed=i < passed, output="3 patients" if i < passed else "About 2.5",
                 status="completed", latency_ms=p50,
                 judge=judge(9 if i < passed else 4, "Matches the expected whole-patient answer." if i < passed else "Does not round to whole patients."))
            for i in range(6)]
    return dict(model_id=model, successful_cases=passed, attempted_cases=6, success_rate=passed / 6,
                wilson_95=[max(0, passed / 6 - .25), min(1, passed / 6 + .12)], p50_ms=p50, p95_ms=p95, judge_mean=grade, judge_count=6,
                quality_dimensions=dict(correctness=dict(mean=grade, count=6), faithfulness=dict(mean=grade - .6, count=6)),
                metrics=dict(schema_rate=1 if passed == 6 else .833, error_rate=0, provider_cost_per_success=None, field_micro_f1=.912),
                results=rows)


BENCH = dict(
    run_id="22222222-2222-4222-8222-222222222222", started_at=(now - timedelta(days=1)).isoformat(), model_id="Qwen3 4B / Gemma 4 E4B",
    runs=[run("gemma4:e4b", 6, 2400, 3900, 8.7), run("qwen3:4b", 4, 3900, 6100, 6.9)],
    pairs=[dict(first="gemma4:e4b", second="qwen3:4b", first_only=2, second_only=0, p=.5, holm_p=.5)],
    ranking=dict(gates=dict(min_success=80, min_schema=95, max_p95_seconds=None), weights=dict(quality=50, latency=20, reliability=10),
                 entries=[dict(model="gemma4:e4b", reasons=[], score=100),
                          dict(model="qwen3:4b", reasons=["Task success below threshold", "Schema compliance below threshold or unavailable"], score=None)]),
    comparison_summary=dict(model="gpt-oss:20b", text="Gemma 4 E4B passed all six matched cases and cleared every threshold. "
                            "Qwen3 4B missed two cases, so it was not ranked."))
HISTORY = [
    dict(run_id=CHAT["run_id"], started_at=CHAT["started_at"], model_id=CHAT["model_id"], title=PROMPT[:75], parent_id=None, pinned=True),
    dict(run_id=BENCH["run_id"], started_at=BENCH["started_at"], model_id=BENCH["model_id"]),
    *[dict(run_id=f"3333333{i}-3333-4333-8333-333333333333", started_at=(now - timedelta(days=i + 2)).isoformat(),
           model_id="Qwen3 4B / Gemma 4 E4B", title=title, parent_id=None)
      for i, title in enumerate(["Merge overlapping intervals in Python", "Extract payer and total as JSON", "Local vs hosted for support triage"])],
]
TRENDS = [dict(model="gemma4:e4b", runs=4, attempts=24, passed=22, graded=24, mean_grade=8.6, median_ms=2500),
          dict(model="qwen3:4b", runs=4, attempts=24, passed=15, graded=22, mean_grade=6.4, median_ms=4100)]


def page(browser, theme):
    context = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2, color_scheme=theme)
    p = context.new_page()
    p.route("**/studio/models", lambda r: r.fulfill(json=MODELS))
    p.route("**/studio/history", lambda r: r.fulfill(json=HISTORY))
    p.route("**/studio/history/1111*", lambda r: r.fulfill(json=CHAT))
    p.route("**/studio/history/2222*", lambda r: r.fulfill(json=BENCH))
    p.route("**/studio/analytics/benchmarks", lambda r: r.fulfill(json=TRENDS))
    p.route("**/studio/live/prompt", lambda r: r.fulfill(content_type="application/x-ndjson",
                                                         body=json.dumps(dict(event="complete", report=CHAT)) + "\n"))
    p.goto(URL)
    return p


def shot(p, name):
    p.wait_for_timeout(600)
    p.screenshot(path=OUT / f"web_{name}.png")
    print("wrote", f"docs/images/web_{name}.png")


def ask(p):
    p.get_by_label("What should the models solve?").fill(PROMPT)
    p.get_by_role("button", name="Send").click()
    p.locator(".response").nth(1).wait_for()


with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=os.getenv("CHROMIUM_PATH"))
    OUT.mkdir(parents=True, exist_ok=True)

    p = page(browser, "dark")
    ask(p)
    p.locator(".response summary").nth(1).click()
    shot(p, "prompt_lab")
    p.get_by_role("button", name="Benchmark").click()
    shot(p, "benchmark")
    p.get_by_role("button", name="History").click()
    p.get_by_role("button", name="Analyze saved benchmarks").click()
    shot(p, "history")
    p.locator("button.history").nth(1).click()
    p.get_by_text("Provisional ranking").wait_for()
    p.locator("main").evaluate("m => m.scrollTo(0, 150)")
    shot(p, "results")

    p = page(browser, "light")
    ask(p)
    p.get_by_role("button", name="Results", exact=True).click()
    p.get_by_text("Answer quality", exact=True).wait_for()
    shot(p, "light")
    browser.close()
