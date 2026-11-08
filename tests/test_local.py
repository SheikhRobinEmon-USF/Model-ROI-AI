from unittest.mock import patch
import pytest
from app.providers.local import generate

def test_local_usage_and_provenance():
    with patch('app.providers.local.request',side_effect=[{'models':[{'name':'qwen3:4b','digest':'sha256:test'}]}, {'done':True,'message':{'content':'{}'},'eval_count':3}]) as call:
        result=generate('qwen3:4b','hello')
        assert result['model_digest']=='sha256:test'
        assert result['input_tokens'] is None
        assert result['total_compute_cost_usd'] is None
        assert call.call_args.args[1]['stream'] is False

def test_no_automatic_download_or_fallback():
    with patch('app.providers.local.request',return_value={'models':[]}) as call:
        with pytest.raises(ValueError,match='not installed'):
            generate('absent','hello')
        assert call.call_count==1

def test_phi_alias_is_used_for_dispatch():
    with patch('app.providers.local.request', side_effect=[
        {'models':[{'name':'phi4-mini:latest','digest':'installed'}]},
        {'done':True,'model':'phi4-mini:latest','message':{'content':'hello'}}
    ]) as call:
        assert generate('phi4-mini:3.8b','question')['model_digest']=='installed'
        assert call.call_args.args[1]['model']=='phi4-mini:latest'


def test_extended_chat_budget(monkeypatch):
    from app.chat_context import chat_budget
    monkeypatch.setenv("MODELROI_CHAT_CONTEXT", "extended")
    assert chat_budget().turns == 12 and chat_budget().characters == 8000
    with patch('app.providers.local.request', side_effect=[
        {'models': [{'name':'qwen3:4b'}]}, {'done': True, 'message': {'content':'ok'}}
    ]) as call:
        generate('qwen3:4b', 'continue', [{'role':'user','content':'earlier'}])
    assert call.call_args.args[1]['options']['num_ctx'] == 8192
