"""Local-only model probe. No remote URL or paid-provider fallback."""
from app.chat_context import chat_budget
from app.execution.performance import current
import argparse
import json
from time import perf_counter
from urllib.request import Request, build_opener, ProxyHandler

BASE = 'http://127.0.0.1:11434'

def request(path, body=None, timeout=180):
    data = None if body is None else json.dumps(body).encode()
    req = Request(BASE+path, data=data, headers={'Content-Type':'application/json'})
    # Ignore proxy environment variables for private local prompts.
    with build_opener(ProxyHandler({})).open(req, timeout=timeout) as response:
        return json.load(response)

def installed_match(model, installed):
    aliases = [model]
    if model == 'phi4-mini:3.8b':
        aliases.extend(['phi4-mini:latest', 'phi4-mini'])
    for alias in aliases:
        for entry in installed:
            if alias in (entry.get('name'), entry.get('model')):
                return entry
    return None

def generate(model, prompt, history=(), *, keep_alive=0):
    state = current.get()
    if state is None or state.inventory is None:
        installed = request('/api/tags').get('models', [])
        if state is not None:
            state.inventory = installed
    else:
        installed = state.inventory
    match = installed_match(model, installed)
    if match is None:
        raise ValueError(f'{model} is not installed. In Terminal run: ollama pull {model}')
    start = perf_counter()
    options = {'temperature': 0, 'num_ctx': chat_budget().tokens if history else 4096, 'num_predict': 512}
    payload = {'model': match.get('name') or match['model'], 'messages': [*history, {'role': 'user', 'content': prompt}],
               'stream': False, 'options': options, 'keep_alive': keep_alive}
    # Phi has no configurable thinking mode.
    if model.split(':')[0] != 'phi4-mini':
        payload['think'] = False
    result = request('/api/chat', payload)
    if not result.get('done'):
        raise ValueError('Incomplete local generation')
    return {'evidence_type':'local_inference','model_id':result.get('model',model),
        'model_digest':match.get('digest'),'output':result['message']['content'],
        'input_tokens':result.get('prompt_eval_count'),'output_tokens':result.get('eval_count'),
        'latency_ms':(perf_counter()-start)*1000,'provider_api_cost_usd':0,
        'total_compute_cost_usd':None,'cost_note':'Local electricity and hardware cost not measured',
        'done_reason':result.get('done_reason'),'settings':{**options,'think':payload.get('think')}}

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--model', default='qwen3:4b')
    args=parser.parse_args()
    print(json.dumps(generate(args.model,'Return only JSON: {"status":"ok"}'),indent=2))
