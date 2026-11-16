"""Fixed hosted routes. Credentials stay in the server environment."""
import json
import os
import re
from time import perf_counter, sleep
from typing import NamedTuple
from urllib.error import HTTPError
from urllib.request import Request, urlopen


class Route(NamedTuple):
    provider: str
    label: str
    base: str
    key: str


GROQ = "https://api.groq.com/openai/v1"
JUDGE = "openai/gpt-oss-120b"
ROUTES = {
    "gemini-3.5-flash-lite": Route("Google", "Gemini Flash-Lite", "https://generativelanguage.googleapis.com/v1beta/openai", "GEMINI_API_KEY"),
    "qwen/qwen3.8-27b": Route("Groq", "Qwen 3.8 27B", GROQ, "GROQ_API_KEY"),
    "google/gemma-4-26b-a4b-it:free": Route("OpenRouter", "Gemma 4 26B", "https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
    "mistral-small-latest": Route("Mistral", "Mistral Small", "https://api.mistral.ai/v1", "MISTRAL_API_KEY"),
    "@cf/meta/llama-3.3-70b-instruct-fp8-fast": Route("Cloudflare", "Llama 3.3 70B", "https://api.cloudflare.com/client/v4/accounts/{account}/ai/v1", "CLOUDFLARE_API_TOKEN"),
}
JUDGE_ROUTE = Route("Groq", "GPT-OSS 120B", GROQ, "GROQ_API_KEY")


def configured(route):
    return bool(os.getenv(route.key)) and (route.provider != "Cloudflare" or
        bool(re.fullmatch(r"[a-fA-F0-9]{32}", os.getenv("CLOUDFLARE_ACCOUNT_ID", ""))))


def completion(model, messages, limit, schema=None):
    route = JUDGE_ROUTE if model == JUDGE else ROUTES[model]
    if not configured(route):
        raise ValueError(f"Configure {route.provider} credentials in the launcher environment.")
    endpoint = route.base.format(account=os.getenv("CLOUDFLARE_ACCOUNT_ID", "")) + "/chat/completions"
    payload = {"model": model, "messages": messages, "max_tokens": limit}
    if schema:
        payload["response_format"] = {"type": "json_schema", "json_schema": {
            "name": "answer_grade", "strict": True, "schema": schema}}
    if model == JUDGE:
        payload["reasoning_effort"] = "low"
    req = Request(endpoint, data=json.dumps(payload).encode(), headers={
        "Content-Type": "application/json", "Authorization": "Bearer " + os.environ[route.key]})
    for attempt in range(2):
        try:
            with urlopen(req, timeout=120) as response:
                result = json.load(response)
            break
        except HTTPError as exc:
            delay = exc.headers.get("Retry-After", "")
            if exc.code == 429 and not attempt and delay.isdigit() and int(delay) <= 60:
                sleep(max(1, int(delay)))
                continue
            raise ValueError(f"{route.provider} returned HTTP {exc.code}. Check model access, credentials and quota.") from None
    choices = result.get("choices") or []
    if not choices or not isinstance(choices[0].get("message", {}).get("content"), str):
        raise ValueError(f"{route.provider} returned no text answer.")
    choice = choices[0]
    if not choice["message"]["content"].strip():
        raise ValueError(f"{route.provider} returned an empty answer.")
    return choice, result


def generate(model, prompt, history=()):
    start = perf_counter()
    choice, result = completion(model, [*history, {"role":"user", "content":prompt}], 1024)
    usage = result.get("usage") or {}
    return {"model_id": result.get("model") or model, "provider": ROUTES[model].provider,
            "evidence_type": "hosted_inference", "output": choice["message"]["content"],
            "done_reason": choice.get("finish_reason"), "input_tokens": usage.get("prompt_tokens"),
            "output_tokens": usage.get("completion_tokens"), "latency_ms": (perf_counter()-start)*1000,
            "provider_api_cost_usd": None}
