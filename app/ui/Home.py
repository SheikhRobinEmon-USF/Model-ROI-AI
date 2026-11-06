import json
import os
from pathlib import Path
import pandas as pd
import streamlit as st
from app.evaluation import run_demo
from app.providers.local import request, generate
from app.datasets.validate import validate_jsonl
from app.execution.local_run import run

st.set_page_config(page_title='ModelROI | Evaluation studio',page_icon='◈',layout='wide')
st.markdown('''<style>
.stApp {background:#f5f7fb;} h1,h2,h3 {color:#14243c;letter-spacing:-.035em;}
[data-testid="stSidebar"] {background:#101e32;}
[data-testid="stSidebar"] * {color:#e3eaf5;}
[data-testid="stMetric"] {background:white;border:1px solid #e2e8f0;border-radius:14px;padding:18px;}
.stButton>button[kind="primary"] {background:#2158df;border:0;border-radius:9px;}
.block-container {padding-top:2.5rem;max-width:1280px;}
</style>''',unsafe_allow_html=True)
local_enabled=os.getenv('MODELROI_ENABLE_LOCAL','false').lower()=='true'
with st.sidebar:
    st.title('◈ ModelROI')
    st.caption('MODEL EVALUATION STUDIO')
    page=st.radio('Workspace',['Overview','Prompt lab','Benchmark','Results'])
    st.divider()
    st.write('Qwen3 4B')
    st.caption('Local inference • No paid APIs')
    st.caption('Local execution enabled' if local_enabled else 'Public preview: mock execution only')

st.caption('MODELROI AI / '+page.upper())
st.title({'Overview':'Evidence before intuition.','Prompt lab':'Put your prompt to the test.',
          'Benchmark':'Measure a complete workload.','Results':'Understand every outcome.'}[page])

if page=='Overview':
    st.write('Test Qwen3 locally, inspect exact grading decisions, and export reproducible evaluation evidence.')
    cols=st.columns(3)
    cols[0].metric('Draft evaluation cases','50')
    cols[1].metric('Task categories','3')
    cols[2].metric('Paid API calls','Disabled')
    st.subheader('A clear path from prompt to evidence')
    a,b,c=st.columns(3)
    a.info('1 · Explore\n\nTry a prompt and inspect the model response.')
    b.info('2 · Evaluate\n\nRun a fixed workload with exact JSON grading.')
    c.info('3 · Inspect\n\nReview failures, uncertainty, and downloadable evidence.')
    st.warning('Development preview. Cases await independent review. No measured model ranking is published.')
    if st.button('Run instant mock demo',type='primary'):
        st.session_state.result=run_demo()
        st.success('Mock completed. Open Results to inspect it.')

elif page=='Prompt lab':
    st.write('Your prompt is sent to Ollama on this machine. No cloud provider is contacted.')
    if not local_enabled:
        st.info('Enable local execution using the instructions in SETUP.md.')
    prompt=st.text_area('Prompt',value='Extract invoice_id and amount as strings. Invoice INV-101, total USD 42.50. Return only JSON.',height=180,max_chars=8000)
    if st.button('Generate with Qwen3 4B',type='primary',disabled=not local_enabled or not prompt.strip()):
        try:
            with st.spinner('Generating locally…'):
                result=generate('qwen3:4b',prompt)
            st.session_state.prompt_result=result
        except Exception as exc:
            st.error(f'Local inference failed ({type(exc).__name__}). Check that Ollama is running and qwen3:4b is installed.')
    if 'prompt_result' in st.session_state:
        result=st.session_state.prompt_result
        st.subheader('Model response')
        st.code(result['output'],language=None)
        st.caption(f"Elapsed: {result['latency_ms']/1000:.2f}s • Output tokens: {result['output_tokens']}")
        with st.expander('Provenance and settings'):
            st.json(result)

elif page=='Benchmark':
    path=Path(__file__).resolve().parents[2]/'datasets/v1/draft_cases.jsonl'
    cases=validate_jsonl(path.read_bytes())
    category=st.selectbox('Workload',['All categories']+sorted({c.task_type for c in cases}))
    selected=[c for c in cases if category=='All categories' or c.task_type==category]
    count=st.slider('Cases to run',1,len(selected),min(5,len(selected)))
    st.caption('Sequential execution • 4,096-token context • 512-token output limit • No retries')
    st.dataframe(pd.DataFrame([{'Case':c.case_id,'Task':c.task_type,'Review':c.review_status} for c in selected[:count]]),hide_index=True,width='stretch')
    st.warning('Hospital cases are synthetic arithmetic fixtures, not verified CMS evidence. A full 50-case run can take several minutes on CPU.')
    if st.button('Run local benchmark',type='primary',disabled=not local_enabled):
        try:
            installed=request('/api/tags').get('models',[])
            if not any(m.get('name')=='qwen3:4b' for m in installed):
                raise ValueError('Install qwen3:4b first')
            bar=st.progress(0)
            st.session_state.result=run(selected[:count],progress=lambda done,total:bar.progress(done/total))
            st.success('Run finished. Open Results for the evidence and downloads.')
        except Exception as exc:
            st.error(f'Cannot run benchmark: {type(exc).__name__}. Check Ollama installation and model availability.')

else:
    result=st.session_state.get('result')
    if not result:
        st.info('Run a mock demo or local benchmark first.')
    else:
        st.caption('Evidence: '+result['evidence_type'])
        a,b,c=st.columns(3)
        a.metric('Task success',f"{result['success_rate']:.0%}")
        b.metric('Cases',str(result['attempted_cases']))
        c.metric('Provider API fees','$0.00')
        interval=result['wilson_95']
        st.write(f'95% Wilson interval: {interval[0]:.1%} to {interval[1]:.1%}')
        st.warning('Provisional evidence. Local hardware cost is unmeasured; latency is exploratory. Mock timings are not model performance.')
        rows=result['results']
        failures=st.checkbox('Show failures only')
        shown=[r for r in rows if not r['passed']] if failures else rows
        st.dataframe(pd.DataFrame(shown),hide_index=True,width='stretch')
        if shown:
            selected=st.selectbox('Inspect case',[r['case_id'] for r in shown])
            row=next(r for r in shown if r['case_id']==selected)
            left,right=st.columns(2)
            left.write('Expected');left.json(row['expected']) if isinstance(row['expected'],dict) else left.code(row['expected'])
            right.write('Model output');right.code(row['output'],language=None)
        st.download_button('Download full JSON',json.dumps(result,indent=2),'modelroi-run.json','application/json')
        st.download_button('Download case CSV',pd.DataFrame(rows).to_csv(index=False),'modelroi-cases.csv','text/csv')
