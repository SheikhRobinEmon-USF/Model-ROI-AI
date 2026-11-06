import asyncio
from types import SimpleNamespace as N
from unittest.mock import AsyncMock
from app.providers.adapters import OpenAIAdapter,AnthropicAdapter

def test_openai_missing_usage():
    create=AsyncMock(return_value=N(output_text='{}',model='test',usage=None))
    result=asyncio.run(OpenAIAdapter(N(responses=N(create=create))).generate('test','hello'))
    assert result.input_tokens is None
    assert result.usage_status=='unavailable'
    assert create.await_count==1

def test_anthropic_text_and_usage():
    create=AsyncMock(return_value=N(content=[N(type='text',text='{}')],model='test',usage=N(input_tokens=12,output_tokens=3)))
    result=asyncio.run(AnthropicAdapter(N(messages=N(create=create))).generate('test','hello'))
    assert result.output=='{}'
    assert result.input_tokens==12
    assert result.output_tokens==3
