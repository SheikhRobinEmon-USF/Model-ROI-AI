from unittest.mock import patch
from app.ui.prompt_compare import evaluate

def test_custom_prompt_preserved_across_partial_failure():
    with patch('app.ui.prompt_compare.generate', side_effect=[
        {'output':'a','latency_ms':300}, ValueError('gemma4:e4b is not installed')
    ]) as generate:
        report=evaluate('Which cities?', ['qwen3:4b','gemma4:e4b'])
    assert [c.args[1] for c in generate.call_args_list]==['Which cities?']*2
    assert [r['status'] for r in report['answers']]==['Answered','Error']
    assert 'output' not in report['answers'][1]
