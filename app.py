"""
PortfolioPulse — AI-Powered Crypto Portfolio Recommendation Engine
Entry point: session state init + page router + global CSS.
"""
import streamlit as st
import os, sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ─── Ensure project root is on path ─────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ─── Page Config ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="PortfolioPulse",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Global CSS Design System ────────────────────────────────────────
st.markdown("""
<style>
    /* ── Import Fonts ────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    /* ── Global Reset ────────────────────────────────────────── */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0A0A0A !important;
        color: #FFFFFF !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    [data-testid="stAppViewContainer"] > section > div {
        background-color: #0A0A0A !important;
    }

    /* ── Sidebar ─────────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background-color: #0A0A0A !important;
        border-right: 1px solid #222222 !important;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h4,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h5 {
        color: #FFFFFF !important;
    }

    /* ── Header / Top Bar ────────────────────────────────────── */
    header[data-testid="stHeader"] {
        background-color: #0A0A0A !important;
        border-bottom: 1px solid #111111 !important;
    }

    /* ── Typography ──────────────────────────────────────────── */
    h1, h2, h3, h4, h5, h6, p, span, label, div {
        font-family: 'Inter', sans-serif !important;
    }

    [data-testid="stMarkdownContainer"] p {
        color: #A0A0A0;
    }

    /* ── Primary Button ──────────────────────────────────────── */
    button[kind="primary"],
    .stButton > button[kind="primary"],
    [data-testid="stBaseButton-primary"] {
        background: #00FF94 !important;
        color: #0A0A0A !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.5rem !important;
        font-size: 14px !important;
        transition: all 0.2s ease !important;
        font-family: 'Inter', sans-serif !important;
    }
    button[kind="primary"]:hover,
    [data-testid="stBaseButton-primary"]:hover {
        background: #00C46A !important;
        box-shadow: 0 0 20px #00FF9440 !important;
        transform: translateY(-1px) !important;
    }

    /* ── Secondary / Outline Button ──────────────────────────── */
    button[kind="secondary"],
    .stButton > button[kind="secondary"],
    .stButton > button:not([kind="primary"]),
    [data-testid="stBaseButton-secondary"] {
        background: transparent !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border: 1px solid #222222 !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.5rem !important;
        font-size: 14px !important;
        transition: all 0.2s ease !important;
        font-family: 'Inter', sans-serif !important;
    }
    button[kind="secondary"]:hover,
    .stButton > button:not([kind="primary"]):hover,
    [data-testid="stBaseButton-secondary"]:hover {
        border-color: #00FF94 !important;
        color: #00FF94 !important;
        box-shadow: 0 0 15px #00FF9420 !important;
    }

    /* ── Disabled Button ─────────────────────────────────────── */
    button:disabled,
    .stButton > button:disabled {
        opacity: 0.35 !important;
        cursor: not-allowed !important;
    }

    /* ── Text Inputs ─────────────────────────────────────────── */
    [data-testid="stTextInput"] input,
    .stTextInput > div > div > input,
    [data-testid="stNumberInput"] input {
        background-color: #111111 !important;
        color: #FFFFFF !important;
        border: 1px solid #222222 !important;
        border-radius: 8px !important;
        font-family: 'JetBrains Mono', monospace !important;
        padding: 10px 14px !important;
    }
    [data-testid="stTextInput"] input:focus,
    .stTextInput > div > div > input:focus {
        border-color: #00FF94 !important;
        box-shadow: 0 0 10px #00FF9420 !important;
    }

    /* ── Select Box ──────────────────────────────────────────── */
    [data-testid="stSelectbox"] > div > div {
        background-color: #111111 !important;
        border: 1px solid #222222 !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
    }

    /* ── Tabs ────────────────────────────────────────────────── */
    [data-testid="stTabs"] button {
        color: #A0A0A0 !important;
        font-weight: 600 !important;
        border-bottom: 2px solid transparent !important;
        background: transparent !important;
    }
    [data-testid="stTabs"] button[aria-selected="true"] {
        color: #00FF94 !important;
        border-bottom-color: #00FF94 !important;
    }

    /* ── Progress Bar ────────────────────────────────────────── */
    [data-testid="stProgress"] > div > div {
        background-color: #1A1A1A !important;
    }
    [data-testid="stProgress"] > div > div > div {
        background: linear-gradient(90deg, #00FF94, #00C46A) !important;
    }

    /* ── Dividers ────────────────────────────────────────────── */
    hr {
        border-color: #222222 !important;
    }

    /* ── Download Button ─────────────────────────────────────── */
    [data-testid="stDownloadButton"] > button {
        background: transparent !important;
        color: #FFFFFF !important;
        border: 1px solid #222222 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    [data-testid="stDownloadButton"] > button:hover {
        border-color: #00FF94 !important;
        color: #00FF94 !important;
    }

    /* ── Spinner ──────────────────────────────────────────────── */
    .stSpinner > div {
        border-top-color: #00FF94 !important;
    }

    /* ── Warnings / Errors ───────────────────────────────────── */
    [data-testid="stAlert"] {
        background-color: #1A1A1A !important;
        border-radius: 8px !important;
    }

    /* ── Hide Streamlit branding ─────────────────────────────── */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    [data-testid="stToolbar"] { display: none; }

    /* ── Scrollbar ────────────────────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #0A0A0A; }
    ::-webkit-scrollbar-thumb { background: #222222; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #333333; }

    /* ── Remove label spacing ────────────────────────────────── */
    [data-testid="stWidgetLabel"] { display: none; }

    /* ── Number Input ────────────────────────────────────────── */
    [data-testid="stNumberInput"] button {
        background: #1A1A1A !important;
        color: #00FF94 !important;
        border: 1px solid #222222 !important;
    }
</style>
""", unsafe_allow_html=True)

# ─── Session State Init ─────────────────────────────────────────────
DEFAULTS = {
    'current_page':        'landing',
    'entry_method':         None,
    'quiz_answers':         {},
    'quiz_current_q':       0,
    'quiz_complete':        False,
    'import_method':        None,
    'wallet_address':       None,
    'risk_score':           None,
    'risk_label':           None,
    'proxy_user_idx':       None,
    'market_state':         None,
    'market_metrics':       {},
    'recommendations':      [],
    'regime_explanation':   None,
    'results_generated_at': None,
}

for key, default in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─── Page Router ─────────────────────────────────────────────────────
page = st.session_state.get('current_page', 'landing')

if page == 'landing':
    from pages.landing import render
    render()
elif page == 'onboarding':
    from pages.onboarding import render
    render()
elif page == 'quiz':
    from pages.quiz import render
    render()
elif page == 'import':
    from pages.import_page import render
    render()
elif page == 'results':
    from pages.results import render
    render()
else:
    st.session_state['current_page'] = 'landing'
    st.rerun()
