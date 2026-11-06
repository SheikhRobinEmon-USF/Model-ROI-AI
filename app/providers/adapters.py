"""Private adapter primitives; paid HTTP routes remain disabled pending runner gates."""
from dataclasses import dataclass
from time import perf_counter

@dataclass(frozen=True)
class Generation:
    output: str
    model_id: str
    input_tokens: int | None
    output_tokens: int | None
    latency_ms: float
    request_id: str | None
    usage_status: str

class OpenAIAdapter:
    def __init__(self, client=None):
        if client is None:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(max_retries=0, timeout=30)
        self.client = client

    async def generate(self, model_id, prompt, max_output_tokens=512):
        if not 1 <= max_output_tokens <= 4096:
            raise ValueError('Output limit must be 1–4096')
        start=perf_counter()
        result=await self.client.responses.create(model=model_id,input=prompt,max_output_tokens=max_output_tokens)
        usage=getattr(result,'usage',None)
        return Generation(result.output_text,result.model,getattr(usage,'input_tokens',None),getattr(usage,'output_tokens',None),(perf_counter()-start)*1000,getattr(result,'_request_id',None),'provider_reported' if usage else 'unavailable')

class AnthropicAdapter:
    def __init__(self, client=None):
        if client is None:
            from anthropic import AsyncAnthropic
            client=AsyncAnthropic(max_retries=0,timeout=30)
        self.client=client

    async def generate(self,model_id,prompt,max_output_tokens=512):
        if not 1 <= max_output_tokens <= 4096:
            raise ValueError('Output limit must be 1–4096')
        start=perf_counter()
        result=await self.client.messages.create(model=model_id,messages=[{'role':'user','content':prompt}],max_tokens=max_output_tokens)
        usage=getattr(result,'usage',None)
        return Generation(''.join(block.text for block in result.content if block.type=='text'),result.model,getattr(usage,'input_tokens',None),getattr(usage,'output_tokens',None),(perf_counter()-start)*1000,getattr(result,'_request_id',None),'provider_reported' if usage else 'unavailable')
