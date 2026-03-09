"""
01_onboarding.py — Quiz vs Import choice screen.
"""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def render():
    # ── Hide sidebar ─────────────────────────────────────────────
    st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none; }
        .block-container { padding-top: 2rem !important; max-width: 900px; }
    </style>
    """, unsafe_allow_html=True)

    # ── Header ───────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align: center; margin-bottom: 48px;">
        <h1 style="
            font-size: 42px; font-weight: 700; color: white;
            margin-bottom: 12px;
        ">How would you like to start?</h1>
        <p style="font-size: 16px; color: #A0A0A0;">
            Choose your path to personalized crypto recommendations
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Two Choice Cards ─────────────────────────────────────────
    col1, col2 = st.columns(2, gap="large")

    card_css = """
        background: #111111; border: 1px solid #222222;
        border-radius: 12px; padding: 40px 28px; text-align: center;
        cursor: pointer; transition: all 0.3s ease; height: 100%;
        min-height: 380px;
    """

    with col1:
        st.markdown(f"""
        <div style="{card_css}" 
             onmouseover="this.style.borderColor='#00FF94'; this.style.boxShadow='0 0 20px #00FF9420';"
             onmouseout="this.style.borderColor='#222222'; this.style.boxShadow='none';">
            <div style="font-size: 48px; margin-bottom: 20px;">📋</div>
            <h2 style="color: white; font-size: 22px; font-weight: 700; margin-bottom: 8px;">
                Risk Assessment Quiz
            </h2>
            <p style="color: #A0A0A0; font-size: 14px; margin-bottom: 24px;">
                Answer 6 questions to determine your risk profile
            </p>
            <div style="text-align: left; margin: 0 auto; max-width: 260px;">
                <p style="color: #00FF94; font-size: 14px; margin: 8px 0;">
                    ✓ No account needed
                </p>
                <p style="color: #00FF94; font-size: 14px; margin: 8px 0;">
                    ✓ Takes ~2 minutes
                </p>
                <p style="color: #00FF94; font-size: 14px; margin: 8px 0;">
                    ✓ Great for beginners
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        if st.button("Start Quiz →", key="start_quiz", use_container_width=True, type="primary"):
            st.session_state['entry_method'] = 'quiz'
            st.session_state['current_page'] = 'quiz'
            st.rerun()

    with col2:
        st.markdown(f"""
        <div style="{card_css}"
             onmouseover="this.style.borderColor='#00FF94'; this.style.boxShadow='0 0 20px #00FF9420';"
             onmouseout="this.style.borderColor='#222222'; this.style.boxShadow='none';">
            <div style="font-size: 48px; margin-bottom: 20px;">👛</div>
            <h2 style="color: white; font-size: 22px; font-weight: 700; margin-bottom: 8px;">
                Import Your Portfolio
            </h2>
            <p style="color: #A0A0A0; font-size: 14px; margin-bottom: 24px;">
                Connect exchange or paste wallet address
            </p>
            <div style="text-align: left; margin: 0 auto; max-width: 260px;">
                <p style="color: #00FF94; font-size: 14px; margin: 8px 0;">
                    ✓ More personalized
                </p>
                <p style="color: #00FF94; font-size: 14px; margin: 8px 0;">
                    ✓ Uses your real patterns
                </p>
                <p style="color: #00FF94; font-size: 14px; margin: 8px 0;">
                    ✓ Supports Coinbase, Binance, MetaMask
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        if st.button("Import Portfolio →", key="start_import", use_container_width=True):
            st.session_state['entry_method'] = 'import'
            st.session_state['current_page'] = 'import'
            st.rerun()

    # ── Back to Home ─────────────────────────────────────────────
    st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
    col_back = st.columns([1, 2, 1])[1]
    with col_back:
        if st.button("← Back to Home", key="back_home", use_container_width=True):
            st.session_state['current_page'] = 'landing'
            st.rerun()
