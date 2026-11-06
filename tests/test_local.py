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
