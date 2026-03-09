"""
02_quiz.py — 6-question risk assessment quiz, one question at a time.
"""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# ─── Quiz Questions ──────────────────────────────────────────────────
QUESTIONS = [
    {
        'id': 'horizon',
        'title': 'Investment Horizon',
        'subtitle': 'How long do you plan to hold your crypto investments?',
        'options': [
            {'key': '<1m',    'label': '⚡ < 1 Month'},
            {'key': '1-6m',   'label': '📅 1–6 Months'},
            {'key': '6m-2y',  'label': '📆 6M–2 Years'},
            {'key': '2y+',    'label': '🏦 2+ Years'},
        ],
    },
    {
        'id': 'loss',
        'title': 'Loss Tolerance',
        'subtitle': 'If your portfolio dropped 30% overnight, what would you do?',
        'options': [
            {'key': 'sell_all',  'label': '🚨 Sell everything'},
            {'key': 'sell_some', 'label': '⚠️ Sell some'},
            {'key': 'hold',      'label': '🧘 Hold and wait'},
            {'key': 'buy_more',  'label': "🛒 Buy more — it's on sale"},
        ],
    },
    {
        'id': 'experience',
        'title': 'Experience Level',
        'subtitle': 'How long have you been investing in crypto?',
        'options': [
            {'key': 'never', 'label': '🌱 Never invested'},
            {'key': '<1y',   'label': '📗 < 1 year'},
            {'key': '1-3y',  'label': '📘 1–3 years'},
            {'key': '3y+',   'label': '🎓 3+ years'},
        ],
    },
    {
        'id': 'volatility',
        'title': 'Volatility Comfort',
        'subtitle': 'How comfortable are you with large price swings?',
        'options': [
            {'key': 'very_uncomfortable', 'label': '😰 Very uncomfortable'},
            {'key': 'somewhat',           'label': '😐 Somewhat uncomfortable'},
            {'key': 'neutral',            'label': '😊 Neutral'},
            {'key': 'comfortable',        'label': '😎 Comfortable'},
        ],
    },
    {
        'id': 'capital',
        'title': 'Capital at Risk',
        'subtitle': 'What percentage of your net worth are you allocating to crypto?',
        'options': [
            {'key': '<5pct',  'label': '🟢 < 5%'},
            {'key': '5-15',   'label': '🟡 5–15%'},
            {'key': '15-30',  'label': '🟠 15–30%'},
            {'key': '30plus', 'label': '🔴 30%+'},
        ],
    },
    {
        'id': 'goal',
        'title': 'Primary Goal',
        'subtitle': 'What best describes your investment objective?',
        'options': [
            {'key': 'preserve',    'label': '🛡️ Preserve wealth'},
            {'key': 'steady',      'label': '📈 Steady growth'},
            {'key': 'aggressive',  'label': '🚀 Aggressive growth'},
            {'key': 'speculation', 'label': '🎲 Speculation'},
        ],
    },
]


def render():
    # ── Hide sidebar + tile button CSS ───────────────────────────
    st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none; }
        .block-container { padding-top: 2rem !important; max-width: 720px; }

        /* Style quiz tile buttons */
        div[data-testid="stVerticalBlock"] div[data-testid="stHorizontalBlock"] .stButton > button {
            min-height: 80px !important;
            font-size: 16px !important;
            font-weight: 600 !important;
            white-space: normal !important;
            line-height: 1.4 !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # ── Init session state ───────────────────────────────────────
    if 'quiz_answers' not in st.session_state:
        st.session_state['quiz_answers'] = {}
    if 'quiz_current_q' not in st.session_state:
        st.session_state['quiz_current_q'] = 0

    total = len(QUESTIONS)
    current_idx = st.session_state['quiz_current_q']

    # ── Safety check ─────────────────────────────────────────────
    if current_idx >= total:
        _complete_quiz()
        return

    question = QUESTIONS[current_idx]

    # ── Progress Bar ─────────────────────────────────────────────
    progress = current_idx / total
    st.progress(progress)
    st.markdown(f"""
    <div style="text-align: right; margin-top: -10px; margin-bottom: 16px;">
        <span style="color: #A0A0A0; font-size: 13px;">Question {current_idx + 1} of {total}</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Question Title ───────────────────────────────────────────
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 32px;">
        <h2 style="color: white; font-size: 32px; font-weight: 700; margin-bottom: 8px;">
            {question['title']}
        </h2>
        <p style="color: #A0A0A0; font-size: 16px;">
            {question['subtitle']}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Option Tiles (as styled Streamlit buttons) ───────────────
    current_answer = st.session_state['quiz_answers'].get(question['id'])
    options = question['options']

    # Row 1
    c1, c2 = st.columns(2, gap="medium")
    for col, opt in zip([c1, c2], options[:2]):
        is_selected = current_answer == opt['key']
        with col:
            btn_label = f"✓ {opt['label']}" if is_selected else opt['label']
            btn_type = "primary" if is_selected else "secondary"
            if st.button(btn_label, key=f"q_{question['id']}_{opt['key']}", use_container_width=True, type=btn_type):
                st.session_state['quiz_answers'][question['id']] = opt['key']
                st.rerun()

    # Row 2
    if len(options) > 2:
        c3, c4 = st.columns(2, gap="medium")
        for col, opt in zip([c3, c4], options[2:4]):
            is_selected = current_answer == opt['key']
            with col:
                btn_label = f"✓ {opt['label']}" if is_selected else opt['label']
                btn_type = "primary" if is_selected else "secondary"
                if st.button(btn_label, key=f"q_{question['id']}_{opt['key']}", use_container_width=True, type=btn_type):
                    st.session_state['quiz_answers'][question['id']] = opt['key']
                    st.rerun()

    # ── Navigation ───────────────────────────────────────────────
    st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)

    nav_col1, nav_spacer, nav_col2 = st.columns([1, 2, 1])

    with nav_col1:
        if current_idx > 0:
            if st.button("← Back", key="quiz_back", use_container_width=True):
                st.session_state['quiz_current_q'] = current_idx - 1
                st.rerun()
        else:
            if st.button("← Exit", key="quiz_exit", use_container_width=True):
                st.session_state['current_page'] = 'onboarding'
                st.rerun()

    with nav_col2:
        has_answer = current_answer is not None
        if current_idx < total - 1:
            if st.button(
                "Continue →",
                key="quiz_next",
                use_container_width=True,
                disabled=not has_answer,
                type="primary",
            ):
                st.session_state['quiz_current_q'] = current_idx + 1
                st.rerun()
        else:
            if st.button(
                "See Results →",
                key="quiz_finish",
                use_container_width=True,
                disabled=not has_answer,
                type="primary",
            ):
                _complete_quiz()


def _complete_quiz():
    """Calculate risk score and navigate to results."""
    from backend.profile_builder import calculate_risk_score, get_risk_label, find_nearest_user
    from backend.market_state import get_market_state
    from backend.inference import get_neumf_recommendations
    from backend.optimization import optimize_portfolio
    from backend.coin_metadata import enrich_recommendations, get_coin_symbol

    answers = st.session_state.get('quiz_answers', {})

    with st.spinner("Consulting AI model..."):
        # ── Step 1: Risk Score ───────────────────────────────────
        risk_score = calculate_risk_score(answers)
        risk_label = get_risk_label(risk_score)
        st.session_state['risk_score'] = risk_score
        st.session_state['risk_label'] = risk_label

        # ── Step 2: Find proxy user ──────────────────────────────
        match = find_nearest_user(risk_score)
        st.session_state['proxy_user_idx'] = match['user_idx']

        # ── Step 3: Market state ─────────────────────────────────
        market = get_market_state()
        st.session_state['market_state'] = market['market_state']
        st.session_state['market_metrics'] = market['market_metrics']

        # ── Step 4: NeuMF inference ──────────────────────────────
        raw_recs = get_neumf_recommendations(match['user_idx'])

        # ── Step 5: Portfolio optimization ───────────────────────
        coin_symbols = {idx: get_coin_symbol(idx) for idx, _ in raw_recs}
        optimized = optimize_portfolio(
            raw_recs,
            market['market_state'],
            risk_score,
            coin_symbols,
        )
        st.session_state['regime_explanation'] = optimized['regime_explanation']

        # ── Step 6: Enrich with metadata ─────────────────────────
        enriched = enrich_recommendations(
            optimized['allocations'],
            market['market_state'],
        )
        st.session_state['recommendations'] = enriched
        st.session_state['quiz_complete'] = True
        st.session_state['entry_method'] = 'quiz'

        import time
        st.session_state['results_generated_at'] = time.strftime('%Y-%m-%d %H:%M:%S')

    # Navigate to results
    st.session_state['current_page'] = 'results'
    st.rerun()
