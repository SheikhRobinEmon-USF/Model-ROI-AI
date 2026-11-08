import json
import os
from playwright.sync_api import sync_playwright
models=[dict(id=m,name=n,installed=True) for m,n in [('qwen3:4b','Qwen3 4B'),('gemma4:e4b','Gemma 4 E4B')]]
with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path=os.getenv("CHROMIUM_PATH"))
    for width in (1280,390,320):
        p=b.new_page(viewport={'width':width,'height':900})
        errors=[]
        p.on('pageerror',lambda e:errors.append(str(e)))
        p.route('**/studio/models',lambda r:r.fulfill(json=models))
        def comparison(route):
            answers=[dict(requested_model=m['id'],status='Answered',output='Response',latency_ms=200,
                          judge=dict(score=0 if m==models[0] else 10,reason='Test judge comment.',scope='Quality',criteria={})) for m in models]
            report=dict(prompt=route.request.post_data_json['prompt'],started_at='2026-11-08T00:00:00Z',
                        run_id='test',answers=answers)
            events=[dict(event='answer',row=row) for row in answers]+[dict(event='complete',report=report)]
            route.fulfill(content_type='application/x-ndjson',body=''.join(json.dumps(e)+'\n' for e in events))
        p.route('**/studio/live/prompt',comparison)
        p.goto('http://127.0.0.1:8598/')
        p.get_by_label('What should the models solve?').fill('Explain the results.')
        p.get_by_role('button',name='Send').click()
        for index,score in enumerate((0,10)):
            answer=p.locator('.response').nth(index)
            toggle=answer.locator('summary')
            toggle.click()
            assert answer.locator('meter').is_visible()
            assert answer.locator('meter').evaluate('m=>m.value')==score
            assert answer.get_by_text('Test judge comment.',exact=True).is_visible()
            assert toggle.bounding_box()['y'] >= answer.locator('pre').bounding_box()['y']
            toggle.press('Enter')
            assert not answer.locator('meter').is_visible()
        assert p.evaluate('document.documentElement.scrollWidth <= window.innerWidth'),width
        editor=p.get_by_label('What should the models solve?')
        editor.fill('Explain again.')
        with p.expect_request('**/studio/live/prompt') as follow_up:
            editor.press('Enter')
        assert follow_up.value.post_data_json['parent_id']=='test'
        p.locator('.chat-turn').nth(1).wait_for()
        p.get_by_role('button',name='New chat').click()
        assert p.locator('.answer-metrics').count()==0
        p.get_by_role('button',name='Benchmark').click()
        p.get_by_label('Evaluation set').select_option('standard')
        assert p.get_by_label('Task category').count()==1
        p.get_by_role('button',name='History').click()
        assert not errors,errors
        print('Browser verified at',width)
        p.close()
    b.close()
