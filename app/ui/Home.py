import json
import streamlit as st
from app.evaluation import run_demo
st.set_page_config(page_title='ModelROI AI', page_icon='📊', layout='wide')
st.title('ModelROI AI')
st.write('Understand model quality, speed, and cost per successful task.')
st.info('Offline foundation preview • Synthetic mock only • No API key required')
if st.button('Run five-case demonstration', type='primary'):
    st.session_state.result = run_demo()
if 'result' in st.session_state:
    result = st.session_state.result
    a,b,c = st.columns(3)
    a.metric('Successful tasks', f"{result['successful_cases']} / {result['attempted_cases']}")
    b.metric('Provider spend', '$0.00')
    c.metric('Evidence', 'Synthetic mock')
    st.write('95% Wilson interval:', ' – '.join(f'{v:.1%}' for v in result['wilson_95']))
    st.warning(result['warning'])
    st.caption('No quality-certified model recommendation is available.')
    st.dataframe(result['results'], use_container_width=True)
    st.download_button('Download JSON evidence', json.dumps(result,indent=2), 'mock-run.json', 'application/json')
else:
    st.write('Run the demonstration to inspect inputs, expected labels, outputs, and grading.')
