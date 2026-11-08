import json
from pathlib import Path

from streamlit.testing.v1 import AppTest

from app.datasets.validate import validate_jsonl
from app.ui.comparison import MODELS, compare, mix_workloads


def test_matched_comparison_and_results_page():
    root = Path(__file__).resolve().parents[1]
    cases = mix_workloads(validate_jsonl((root / 'datasets/v1/draft_cases.jsonl').read_bytes()))[:3]
    assert len({case.task_type for case in cases}) == 3
    calls = []
    def generate(model, prompt):
        case = next(case for case in cases if case.input == prompt)
        calls.append((model, prompt))
        missed = cases[0] if model == 'qwen3:4b' else cases[1]
        return dict(output=json.dumps({} if case == missed else case.expected), latency_ms=100)
    result = compare(cases, list(MODELS), generate_fn=generate)
    assert calls == [(m,c.input) for m in MODELS for c in cases]
    assert [r['successful_cases'] for r in result['runs']] == [2,2]
    app = AppTest.from_file(str(root/'app/ui/Home.py'))
    app.session_state.page = 'Results'
    app.session_state.result = result
    app.run()
    assert not app.exception
    assert len(app.dataframe) >= 3
    assert any('Qwen3 4B and Gemma 4 E4B' in m.value for m in app.markdown)
