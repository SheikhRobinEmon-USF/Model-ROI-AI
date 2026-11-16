"""ModelROI's local, dependency-free visual system."""
import streamlit as st

CSS = '''<style>
:root {color-scheme:light;--ink:#152d35;--muted:#526870;--mint:#087f6d;--line:#dce6e8;}
.stApp {background:#f4f7f8;color:var(--ink);font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;}
[data-testid="stHeader"] {background:#f4f7f8;color:var(--ink);}
[data-testid="stMain"] h1,[data-testid="stMain"] h2,[data-testid="stMain"] h3 {color:var(--ink)!important;letter-spacing:-.045em;font-weight:750;}
[data-testid="stMain"] p,[data-testid="stMain"] label,[data-testid="stMain"] li {color:var(--ink);}
[data-testid="stCaptionContainer"] p {color:#526870!important;}
.block-container {max-width:1320px;padding:3rem 3.2rem 4rem;}
[data-testid="stSidebar"] {background:#102c35;border-right:1px solid #26464f;}
[data-testid="stSidebar"] p,[data-testid="stSidebar"] h1,[data-testid="stSidebar"] label {color:#e8f4f3!important;}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {color:#a8c5c9!important;}
[data-testid="stSidebar"] button {background:transparent;border:1px solid transparent;color:#c7dcdf;width:100%;text-align:left;min-height:46px;border-radius:10px;}
[data-testid="stSidebar"] button:hover {background:#1c414b;border-color:#355963;}
[data-testid="stSidebar"] button[kind="primary"] {background:#214e53;border-color:#458278;box-shadow:inset 3px 0 #79ddc3;}
[data-testid="stMetric"] {background:#fff;border:1px solid var(--line);border-radius:16px;padding:21px 24px;box-shadow:0 5px 20px #13313a05;}
[data-testid="stMetricValue"] {color:var(--ink)!important;font-variant-numeric:tabular-nums;}
[data-testid="stMetricLabel"] p {color:var(--muted)!important;}
.stButton button,.stDownloadButton button {min-height:44px;border-radius:10px;border:1px solid #bccfd2;font-weight:600;transition:transform .16s,box-shadow .16s,background .16s;}
.stButton button:hover,.stDownloadButton button:hover {transform:translateY(-2px);box-shadow:0 7px 18px #10352d12;}
.stButton button[kind="primary"] {background:#087f6d;color:white;border-color:#087f6d;}
.stButton button[kind="primary"] p {color:white!important;}
button:focus-visible,textarea:focus-visible {outline:3px solid #2bac98!important;outline-offset:3px;}
[data-testid="stTextArea"] textarea {background:white!important;color:#152d35!important;border:1px solid #b9cdd1;border-radius:12px;padding:18px;font-family:ui-monospace,SFMono-Regular,monospace;line-height:1.7;}
[data-baseweb="select"]>div {background:#fff;color:#152d35;border-color:#c8d7da;border-radius:10px;}
[data-testid="stExpander"] {background:white;border-color:var(--line);border-radius:12px;}
.roi-hero {position:relative;overflow:hidden;background:linear-gradient(115deg,#102e38,#174b50);padding:38px 40px;border-radius:22px;margin:8px 0 25px;animation:arrive .4s ease-out;}
.roi-hero:after {content:"";position:absolute;width:280px;height:280px;border:1px solid #77c5b62b;border-radius:50%;right:-70px;top:-110px;box-shadow:0 0 0 42px #77c5b60b,0 0 0 84px #77c5b608;pointer-events:none;}
.roi-hero h2 {color:#f3fffc!important;font-size:clamp(1.9rem,3vw,3.1rem);max-width:700px;margin:14px 0!important;line-height:1.12;}
.roi-hero p {color:#bdd6d8!important;max-width:650px;font-size:1.05rem;line-height:1.7;margin-bottom:8px;}
.roi-eyebrow {color:#8fe2cd;font:600 11px ui-monospace,monospace;letter-spacing:.17em;}
.roi-card {background:#fff;border:1px solid var(--line);border-radius:16px;padding:24px;height:205px;transition:transform .2s,border-color .2s;}
.roi-card:hover {transform:translateY(-4px);border-color:#76bbaa;}
.roi-card .step {display:inline-flex;background:#e6f5ef;color:#08745f;border-radius:10px;padding:7px 11px;font:600 13px ui-monospace,monospace;margin-bottom:16px;}
.roi-card h3 {font-size:1.15rem;margin:0 0 9px;letter-spacing:-.02em;}
.roi-card p {color:#526870!important;font-size:.94rem;line-height:1.6;}
.roi-note {border-left:3px solid #b78934;background:#fff8e9;border-radius:0 10px 10px 0;padding:13px 18px;color:#76541c;font-size:.88rem;margin:22px 0;}
.roi-brand {font-size:25px;font-weight:750;letter-spacing:-1px;color:#f2fffb;margin:0 0 5px;}
.roi-brand span {color:#79ddc3;}
.roi-chip {display:inline-block;border:1px solid #bcd5cf;border-radius:20px;padding:5px 12px;color:#39635a;font-size:12px;background:#eff8f4;}
@keyframes arrive {from {opacity:0;transform:translateY(8px)} to {opacity:1;transform:translateY(0)}}
@media(prefers-reduced-motion:reduce) {* {animation:none!important;transition:none!important;scroll-behavior:auto!important;}}
@media(max-width:700px) {.block-container {padding:2rem 1rem}.roi-hero {padding:25px}.roi-card {height:auto;min-height:180px}}
</style>'''

def apply():
    st.markdown(CSS,unsafe_allow_html=True)
