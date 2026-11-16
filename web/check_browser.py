import json
import os
from playwright.sync_api import expect, sync_playwright
models=[dict(id=m,name=n,installed=True) for m,n in [('qwen3:4b','Qwen3 4B'),('gemma4:e4b','Gemma 4 E4B')]]
remote=[dict(id=n,name=n,provider=n,installed=True,judge_ready=True) for n in ("Google","Groq","OpenRouter","Mistral","Cloudflare")]
with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path=os.getenv("CHROMIUM_PATH"))
    for width in (1280,390,320):
        p=b.new_page(viewport={'width':width,'height':900})
        errors=[]
        p.on('pageerror',lambda e:errors.append(str(e)))
        p.route('**/studio/models',lambda r:r.fulfill(json=models+remote))
        saved={}
        p.route('**/studio/history/test*',lambda r:r.fulfill(json=saved[r.request.url.split('/')[-1]]))
        p.route('**/studio/history/*/summary',lambda r:r.fulfill(json={'model':'gpt-oss:20b','text':'Gemma earned the higher grade.'}))
        def comparison(route):
            answers=[dict(requested_model=m['id'],status='Answered',output='Response',latency_ms=200,
                          judge=dict(score=0 if m==models[0] else 10,reason='Test judge comment.',scope='Quality',criteria={})) for m in models+remote if m["id"] in route.request.post_data_json["models"]]
            report=dict(prompt=route.request.post_data_json['prompt'],started_at='2026-11-08T00:00:00Z',
                        run_id='test2' if saved else 'test',parent_id=route.request.post_data_json.get('parent_id'),answers=answers)
            saved[report['run_id']]=report
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
        if width<=720:
            p.get_by_role('button',name='Chat history',exact=True).click()
        p.get_by_role('button',name='Explain the results.',exact=True).click()
        p.locator('.chat-turn').nth(1).wait_for()
        p.get_by_role('button',name='Results',exact=True).click()
        p.get_by_text('Gemma earned the higher grade.').wait_for()
        p.get_by_role('button',name='Benchmark').click()
        p.get_by_label('Evaluation set').select_option('standard')
        assert p.get_by_label('Task category').count()==1
        p.get_by_role('button',name='History').click()
        p.get_by_role('button',name='Prompt lab').click()
        p.get_by_role('button',name='New chat').click()
        p.get_by_role('button',name='Hosted',exact=True).click()
        p.locator('.chat-tools summary').click()
        for label in ('Mistral','Cloudflare'):
            p.get_by_role('checkbox',name=label).check()
        p.locator('.chat-tools summary').click()
        editor.fill('Compare all five.')
        p.get_by_role('button',name='Send').click()
        picker=p.locator('.answer-picker')
        picker.get_by_role('button',name='Cloudflare').click()
        assert picker.locator('button').count()==5
        assert p.locator('.response').count()==1
        assert p.locator('.response strong').first.inner_text()=='Cloudflare'
        assert p.evaluate('document.documentElement.scrollWidth <= innerWidth')
        # Add a model: customize an installed one, then upload a file, then download by name.
        p.get_by_role('button',name='Add model',exact=True).click()
        form=p.get_by_role('dialog',name='Add a model')
        form.get_by_role('tab',name='Customize installed').click()
        form.get_by_label('Model name').fill('Analyst V1')
        form.get_by_label('Model instructions').fill('Explain all assumptions.')
        assert form.get_by_role('button',name='Create model').is_disabled()
        form.get_by_label('Model name').fill('analyst-v1')
        assert form.get_by_role('button',name='Create model').is_enabled()
        form.get_by_role('tab',name='Upload a file').click()
        picker=form.get_by_label('Model file')
        picker.set_input_files(dict(name='notes.gguf',mimeType='application/octet-stream',buffer=b'not a model'))
        form.get_by_text('notes.gguf is not a GGUF model file.').wait_for()
        assert form.get_by_role('button',name='Import model').is_disabled()
        picker.set_input_files(dict(name='My Tuned.v2.gguf',mimeType='application/octet-stream',buffer=b'GGUF'+bytes(256)))
        expect(form.get_by_label('Model name')).to_have_value('my-tuned-v2')
        mine=dict(id='ollama/modelroi/my-tuned-v2:latest',name='modelroi/my-tuned-v2:latest',label='my-tuned-v2',custom=True,installed=True,size=260,quantization='Q4_K_M')
        p.route('**/studio/models/upload*',lambda r:r.fulfill(json=dict(digest='sha256:'+'a'*64,size=260,file='My Tuned.v2.gguf')))
        def register(route):
            assert route.request.post_data_json==dict(name='my-tuned-v2',digest='sha256:'+'a'*64,file='My Tuned.v2.gguf',instructions='')
            p.route('**/studio/models',lambda r:r.fulfill(json=models+remote+[mine]))
            route.fulfill(json=dict(id=mine['id'],name=mine['name']))
        p.route('**/studio/models/import',register)
        form.get_by_role('button',name='Import model').click()
        p.get_by_role('status').filter(has_text='my-tuned-v2 is ready').wait_for()
        assert not form.is_visible()
        p.get_by_role('button',name='Add model',exact=True).click()
        form.get_by_role('tab',name='Download by name').click()
        p.route('**/studio/live/models/pull',lambda r:r.fulfill(content_type='application/x-ndjson',
                body=json.dumps(dict(event='progress',status='pulling abc',completed=5,total=10))+'\n'+json.dumps(dict(event='error',message='Ollama could not download that model: not found'))+'\n'))
        form.get_by_label('Model reference').fill('hf.co/me/missing:Q4_K_M')
        form.get_by_role('button',name='Download model').click()
        assert 'not found' in form.get_by_role('alert').inner_text()
        assert form.get_by_role('button',name='Remove my-tuned-v2').count()==1
        assert p.evaluate('document.documentElement.scrollWidth <= innerWidth')
        form.get_by_role('button',name='Cancel').click()
        p.unroute('**/studio/models')
        p.route('**/studio/models',lambda r:r.fulfill(json=models+remote))
        assert not errors,errors
        print('Browser verified at',width)
        p.close()
    b.close()
