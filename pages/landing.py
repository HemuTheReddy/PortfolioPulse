"""
00_landing.py — Full-viewport hero landing page.
"""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def render():
    # ── Hide sidebar on landing ──────────────────────────────────
    st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none; }
        .block-container { padding-top: 0 !important; max-width: 1200px; }
    </style>
    """, unsafe_allow_html=True)

    # ── Fetch market state for navbar badge ──────────────────────
    from backend.market_state import get_market_state, get_state_emoji, get_state_color
    market = get_market_state()
    state = market['market_state']
    emoji = get_state_emoji(state)
    color = get_state_color(state)

    # ── Navbar ───────────────────────────────────────────────────
    st.markdown(f"""
    <div style="
        display: flex; justify-content: space-between; align-items: center;
        padding: 16px 0; border-bottom: 1px solid #222222; margin-bottom: 40px;
    ">
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="
                width: 32px; height: 32px; border-radius: 50%;
                background: #003D21; border: 2px solid #00FF94;
                display: flex; align-items: center; justify-content: center;
                font-size: 14px;
            ">✓</div>
            <span style="font-size: 20px; font-weight: 800; color: white;">
                Crypto<span style="color: #00FF94;">Sage</span>
            </span>
        </div>
        <div style="
            display: flex; align-items: center; gap: 8px;
            background: {color}15; border: 1px solid {color}40;
            padding: 6px 14px; border-radius: 6px;
        ">
            <span style="font-size: 12px; color: #A0A0A0;">Live:</span>
            <span style="font-size: 14px; font-weight: 700; color: {color};">
                {emoji} {state.upper().replace('_', ' ')}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Hero Section ─────────────────────────────────────────────
    st.markdown("""
    <div style="text-align: center; padding: 40px 0 20px;">
        <div style="
            display: inline-block; background: #003D2130;
            border: 1px solid #00FF9430; border-radius: 20px;
            padding: 6px 16px; margin-bottom: 24px;
        ">
            <span style="font-size: 13px; color: #00FF94; font-weight: 500; letter-spacing: 0.5px;">
                AI-Powered · Real-Time Market Aware
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align: center;">
        <h1 style="
            font-size: 72px; font-weight: 800; line-height: 1.05;
            letter-spacing: -2px; margin: 0 0 24px 0; color: white;
        ">
            Stop Guessing.<br>
            Start Investing<br>
            <span style="color: #00FF94;">Smarter.</span>
        </h1>
        <p style="
            font-size: 18px; color: #A0A0A0; max-width: 640px;
            margin: 0 auto 40px; line-height: 1.7;
        ">
            PortfolioPulse combines behavioral AI trained on 5,000 successful 
            crypto traders with live market intelligence to recommend 
            the right assets at the right time for your risk profile.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── CTA Buttons ──────────────────────────────────────────────
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("Take the 2-Minute Quiz →", key="cta_quiz", use_container_width=True, type="primary"):
                st.session_state['current_page'] = 'onboarding'
                st.rerun()
        with btn_col2:
            if st.button("Import My Portfolio", key="cta_import", use_container_width=True):
                st.session_state['current_page'] = 'import'
                st.session_state['entry_method'] = 'import'
                st.rerun()

    # ── Spacer ───────────────────────────────────────────────────
    st.markdown("<div style='height: 60px;'></div>", unsafe_allow_html=True)

    # ── 3 Feature Cards ─────────────────────────────────────────
    card_style = """
        background: #111111; border: 1px solid #222222;
        border-radius: 12px; padding: 32px 24px; text-align: center;
        transition: all 0.3s ease; height: 100%;
    """

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(f"""
        <div style="{card_style}">
            <div style="font-size: 36px; margin-bottom: 16px;">🧠</div>
            <h3 style="color: white; font-size: 18px; font-weight: 700; margin-bottom: 12px;">
                Trained on Winners
            </h3>
            <p style="color: #A0A0A0; font-size: 14px; line-height: 1.6; margin: 0;">
                AI studied 32,000+ interactions from 5,000 profitable wallets
            </p>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div style="{card_style}">
            <div style="font-size: 36px; margin-bottom: 16px;">📡</div>
            <h3 style="color: white; font-size: 18px; font-weight: 700; margin-bottom: 12px;">
                Live Market Context
            </h3>
            <p style="color: #A0A0A0; font-size: 14px; line-height: 1.6; margin: 0;">
                Recommendations shift in real-time with Bull/Bear/Fear regimes
            </p>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div style="{card_style}">
            <div style="font-size: 36px; margin-bottom: 16px;">⚖️</div>
            <h3 style="color: white; font-size: 18px; font-weight: 700; margin-bottom: 12px;">
                Risk-Adjusted Weights
            </h3>
            <p style="color: #A0A0A0; font-size: 14px; line-height: 1.6; margin: 0;">
                Not just what to buy — how much. Portfolio Theory optimizes weights
            </p>
        </div>
        """, unsafe_allow_html=True)
