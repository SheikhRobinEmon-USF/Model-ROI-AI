"""Invite-only, session-scoped prompt comparisons for a small pilot."""
import hmac
import os
from threading import Lock

import streamlit as st

from app.ui.comparison import MODELS
from app.ui.prompt_compare import display, evaluate

st.set_page_config(page_title="ModelROI | Tester pilot", layout="wide")
st.title("Compare three local models")
secret = os.environ.get("MODELROI_PILOT_CODE", "")
if len(secret) < 16:
    st.error("Start the tester pilot using the launcher.")
    st.stop()
code = st.text_input("Tester access code", type="password")
if not hmac.compare_digest(code.encode(), secret.encode()):
    if code:
        st.error("Check the code supplied by the host.")
    st.stop()

@st.cache_resource
def host_lock():
    return Lock()

prompt = st.text_area("What would you like to ask?", max_chars=2000)
models = st.multiselect("Models", list(MODELS), default=list(MODELS), format_func=MODELS.get)
if st.button("Compare answers", type="primary", disabled=not prompt.strip() or not models):
    lock = host_lock()
    if lock.acquire(blocking=False):
        try:
            with st.spinner("Running your question on the host Mac…"):
                st.session_state.report = evaluate(prompt, models)
        finally:
            lock.release()
    else:
        st.info("Another comparison is running. Please try again shortly.")
if "report" in st.session_state:
    display(st.session_state.report)
