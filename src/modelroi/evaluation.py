"""Offline demonstration. Synthetic answers are never provider evidence."""
import math
import time
from pydantic import BaseModel, ConfigDict

class Case(BaseModel):
    model_config = ConfigDict(extra='forbid')
    case_id: str
    prompt: str
    expected: str

CASES = [Case(case_id=f'demo-{i}', prompt=f'Classify sentiment: {text}', expected=label)
         for i, (text, label) in enumerate([
             ('Excellent service', 'positive'), ('Terrible service', 'negative'),
             ('The package arrived', 'neutral'), ('I love it', 'positive'),
             ('It is broken', 'negative')], 1)]

def wilson(successes: int, n: int):
    if not 0 <= successes <= n:
        raise ValueError('Require 0 <= successes <= n')
    if not n:
        return None
    p, z = successes / n, 1.96
    denominator = 1 + z*z/n
    center = (p + z*z/(2*n))/denominator
    radius = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/denominator
    return [max(0, center-radius), min(1, center+radius)]

def paired_exact(a_only: int, b_only: int):
    if min(a_only, b_only) < 0:
        raise ValueError('Counts cannot be negative')
    n = a_only+b_only
    return min(1.0, 2*sum(math.comb(n, k) for k in range(min(a_only,b_only)+1))/2**n)

def percentile(values, p):
    if not values:
        return None
    if not 0 < p <= 1:
        raise ValueError('p must be in (0,1]')
    return sorted(values)[math.ceil(p*len(values))-1]

def mock_answer(prompt):
    text = prompt.lower()
    if any(word in text for word in ('excellent', 'love')):
        return 'positive'
    if any(word in text for word in ('terrible', 'broken')):
        return 'negative'
    return 'neutral'

def run_demo():
    rows = []
    for case in CASES:
        start = time.perf_counter()
        answer = mock_answer(case.prompt)
        rows.append(dict(case_id=case.case_id, prompt=case.prompt, expected=case.expected,
                         output=answer, passed=answer == case.expected,
                         latency_ms=(time.perf_counter()-start)*1000))
    successes = sum(row['passed'] for row in rows)
    return dict(evidence_type='synthetic_mock', model_id='mock-rules-v1',
                dataset_version='demo-v1', successful_cases=successes, attempted_cases=len(rows),
                success_rate=successes/len(rows), wilson_95=wilson(successes,len(rows)),
                provider_cost_usd=0, p95_ms=percentile([r['latency_ms'] for r in rows],.95),
                warning='Mock execution timings are not model latency. n < 100: exploratory only.',
                recommendation_status='PROVISIONAL_INSUFFICIENT_EVIDENCE', results=rows)

if __name__ == '__main__':
    import json
    print(json.dumps(run_demo(), indent=2))
