import json
from playwright.sync_api import sync_playwright
models=[dict(id=m,name=n,installed=True) for m,n in [('qwen3:4b','Qwen3 4B'),('gemma4:e4b','Gemma 4 E4B'),('phi4-mini:3.8b','Phi-4-mini')]]
with sync_playwright() as pw:
    b=pw.chromium.launch()
    for width in (1280,390,320):
        p=b.new_page(viewport={'width':width,'height':900})
        errors=[]
        p.on('pageerror',lambda e:errors.append(str(e)))
        p.route('**/studio/models',lambda r:r.fulfill(json=models))
        def comparison(route):
            answers=[dict(requested_model=m['id'],status='Answered',output='Response',latency_ms=200,
                          judge=dict(score=7.5,scope='Quality',criteria={})) for m in models]
            report=dict(prompt=route.request.post_data_json['prompt'],started_at='2026-11-08T00:00:00Z',
                        run_id='test',answers=answers)
            events=[dict(event='answer',row=row) for row in answers]+[dict(event='complete',report=report)]
            route.fulfill(content_type='application/x-ndjson',body=''.join(json.dumps(e)+'\n' for e in events))
        p.route('**/studio/live/prompt',comparison)
        p.goto('http://127.0.0.1:8598/')
        p.get_by_label('What should the models solve?').fill('Explain the results.')
        p.get_by_role('button',name='Compare answers').click()
        p.get_by_role('button',name='View metrics').click()
        p.get_by_role('heading',name='Answer quality').wait_for()
        assert p.locator('meter').count()==3
        assert p.evaluate('document.documentElement.scrollWidth <= window.innerWidth'),width
        p.get_by_role('button',name='Close metrics').click()
        p.get_by_role('button',name='Benchmark').click()
        p.get_by_label('Evaluation set').select_option('standard')
        assert p.get_by_label('Task category').count()==1
        p.get_by_role('button',name='History').click()
        assert not errors,errors
        print('Browser verified at',width)
        p.close()
    b.close()
