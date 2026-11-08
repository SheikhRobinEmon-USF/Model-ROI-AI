"""Sequential local evaluation with explicit failures and portable evidence."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from time import perf_counter
from uuid import uuid4
from app.providers.local import generate
from app.graders.exact import grade
from app.evaluation import wilson, percentile

def run(cases, model='qwen3:4b', progress=None, generate_fn=None):
    rows=[]
    started=datetime.now(timezone.utc).isoformat()
    for i,case in enumerate(cases):
        start=perf_counter()
        row={'case_id':case.case_id,'task_type':case.task_type,'input':case.input,
             'expected':case.expected,'review_status':case.review_status}
        try:
            if generate_fn is None:
                response = generate(model, case.input, keep_alive=0 if i + 1 == len(cases) else "15s")
            else:
                response = generate_fn(model, case.input)
            result=grade(case,response['output'])
            if response.get('done_reason')=='length':
                result={'passed':False,'reason':'output_truncated'}
            row.update(response,**result,status='completed')
        except Exception as exc:
            row.update(output='',passed=False,reason='inference_error',status='failed',
                       error_type=type(exc).__name__,latency_ms=(perf_counter()-start)*1000)
        rows.append(row)
        if progress:
            progress(i+1,len(cases))
    n=len(rows)
    successes=sum(r['passed'] for r in rows)
    serialized=json.dumps([c.model_dump() for c in cases],sort_keys=True)
    return {'run_id':str(uuid4()),'started_at':started,'evidence_type':'local_inference',
            'model_id':model,'dataset_sha256':sha256(serialized.encode()).hexdigest(),
            'planned_cases':len(cases),'attempted_cases':n,'successful_cases':successes,
            'success_rate':successes/n if n else None,'wilson_95':wilson(successes,n),
            'p50_ms':percentile([r['latency_ms'] for r in rows],.5),
            'p95_ms':percentile([r['latency_ms'] for r in rows],.95),
            'provider_api_cost_usd':0,'total_compute_cost_usd':None,
            'recommendation_status':'PROVISIONAL_INSUFFICIENT_EVIDENCE',
            'limitations':['Draft labels require independent review.','Local compute cost is unmeasured.',
                          'Latency is hardware-specific; fewer than 100 samples is exploratory.',
                          'Single-model run does not establish comparative superiority.'],
            'results':rows}
