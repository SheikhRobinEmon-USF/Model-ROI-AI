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

    # Regressions: each block pins a bug that once reached users.
    p=b.new_page(viewport={'width':1280,'height':900})
    errors=[]
    p.on('pageerror',lambda e:errors.append(str(e)))
    chat=dict(run_id='chat-1',parent_id=None,prompt='Which is cheaper?',started_at='2026-11-08T00:00:00Z',model_id='Gemma 4 E4B',
              evidence_type='custom_prompt',answers=[dict(requested_model='gemma4:e4b',status='Answered',output='Gemma answer',latency_ms=90)])
    p.route('**/studio/models',lambda r:r.fulfill(json=models+remote))
    p.route('**/studio/history',lambda r:r.fulfill(json=[dict(run_id='chat-1',parent_id=None,title='Which is cheaper?',model_id='Gemma 4 E4B',started_at='2026-11-08T00:00:00Z')]))
    p.route('**/studio/history/chat-1',lambda r:r.fulfill(json=chat))
    p.route('**/studio/history/gone-1',lambda r:r.fulfill(status=404,json={'detail':'Run no longer available.'}))
    p.route('**/studio/history/*/summary',lambda r:r.fulfill(json={'model':'gpt-oss:20b','text':'Summary.'}))
    # A chat deleted since the last visit is forgotten quietly, not reported as an error on startup.
    p.add_init_script("try{if(!sessionStorage.getItem('seeded')){localStorage.setItem('modelroi-chat','gone-1');sessionStorage.setItem('seeded','1')}}catch(e){}")
    p.goto('http://127.0.0.1:8598/')
    p.get_by_role('button',name='Which is cheaper?',exact=True).wait_for()
    assert p.get_by_role('alert').count()==0
    assert p.evaluate("localStorage.getItem('modelroi-chat')") is None
    # Refreshing model status keeps the user's selection.
    picker=p.locator('.chat-tools summary')
    picker.click()
    p.get_by_role('checkbox',name='Qwen3 4B').uncheck()
    p.get_by_role('button',name='Refresh model status').click()
    expect(picker).to_contain_text('Models · 1')
    assert not p.get_by_role('checkbox',name='Qwen3 4B').is_checked() and p.get_by_role('checkbox',name='Gemma 4 E4B').is_checked()
    picker.click()
    # Reopening a chat continues with the models that chat used.
    p.get_by_role('button',name='New chat',exact=True).first.click()
    picker.click(); p.get_by_role('checkbox',name='Qwen3 4B').check(); picker.click()
    p.get_by_role('button',name='Which is cheaper?',exact=True).click()
    p.get_by_text('Gemma answer').wait_for()
    expect(picker).to_contain_text('Models · 1')
    # The server's reason for refusing a run is shown, and the unsent prompt is kept.
    p.route('**/studio/live/prompt',lambda r:r.fulfill(status=409,json={'detail':'Another evaluation is running.'}))
    editor=p.get_by_label('What should the models solve?')
    editor.fill('Follow-up')
    editor.press('Enter')
    expect(p.get_by_role('alert')).to_contain_text('Another evaluation is running.')
    expect(editor).to_have_value('Follow-up')
    # A crash page instead of JSON reads as a server error, not a parsing error.
    p.unroute('**/studio/live/prompt')
    p.route('**/studio/live/prompt',lambda r:r.fulfill(status=500,content_type='text/plain',body='Internal Server Error'))
    editor.press('Enter')
    expect(p.get_by_role('alert')).to_contain_text('HTTP 500')
    # During a run the palette offers only commands that cannot disturb it.
    held=[]
    p.unroute('**/studio/live/prompt')
    p.route('**/studio/live/prompt',lambda r:held.append(r))
    editor.press('Enter')
    p.get_by_role('status').filter(has_text='Generating').wait_for()
    p.keyboard.press('Control+k')
    palette=p.get_by_role('dialog',name='Command palette')
    palette.get_by_label('Search commands and chats').fill('new chat')
    expect(palette.get_by_role('option')).to_have_count(0)
    p.keyboard.press('Escape')
    report=dict(chat,run_id='chat-2',parent_id='chat-1',prompt='Follow-up')
    held[0].fulfill(content_type='application/x-ndjson',body=json.dumps(dict(event='complete',report=report))+'\n')
    p.get_by_role('status').filter(has_text='Generating').wait_for(state='detached')
    # Invalid ranking thresholds are explained and block the run instead of failing on the server.
    p.get_by_role('button',name='Benchmark').click()
    run_button=p.get_by_role('button',name='Run benchmark')
    p.get_by_label('Minimum task success (%)').fill('150')
    expect(p.get_by_role('alert')).to_contain_text('Minimum task success must be a whole number from 0 to 100.')
    assert run_button.is_disabled()
    p.get_by_label('Minimum task success (%)').fill('80')
    assert run_button.is_enabled()
    assert not errors,errors
    print('Regressions verified')
    p.close()
    b.close()
