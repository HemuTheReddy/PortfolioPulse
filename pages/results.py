"""
04_results.py — Main results dashboard with sidebar, stats, recommendations, and charts.
"""
import streamlit as st
import plotly.graph_objects as go
import sys, os, io, csv
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def render():
    from backend.market_state import get_market_state, get_regime_message, get_state_color, get_state_emoji
    from backend.coin_metadata import enrich_recommendations, get_coin_symbol
    from backend.inference import get_neumf_recommendations
    from backend.optimization import optimize_portfolio

    # ── Check data ───────────────────────────────────────────────
    recs = st.session_state.get('recommendations', [])
    if not recs:
        st.warning("No recommendations found. Please complete the quiz or import your portfolio first.")
        if st.button("← Go Back", key="results_back"):
            st.session_state['current_page'] = 'onboarding'
            st.rerun()
        return

    market_state = st.session_state.get('market_state', 'neutral')
    market_metrics = st.session_state.get('market_metrics', {})
    risk_score = st.session_state.get('risk_score', 3)
    risk_label = st.session_state.get('risk_label', 'Moderate')
    entry_method = st.session_state.get('entry_method', 'quiz')
    regime_explanation = st.session_state.get('regime_explanation', '')

    state_color = get_state_color(market_state)
    state_emoji = get_state_emoji(market_state)

    # ── Layout ───────────────────────────────────────────────────
    st.markdown("""
    <style>
        .block-container { max-width: 1200px; padding-top: 1rem !important; }
    </style>
    """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════
    # SIDEBAR
    # ═══════════════════════════════════════════════════════════════
    with st.sidebar:
        # Logo
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 20px;">
            <div style="
                width: 28px; height: 28px; border-radius: 50%;
                background: #003D21; border: 2px solid #00FF94;
                display: flex; align-items: center; justify-content: center;
                font-size: 12px;
            ">✓</div>
            <span style="font-size: 18px; font-weight: 800; color: white;">
                Crypto<span style="color: #00FF94;">Sage</span>
            </span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # ── Market Pulse ─────────────────────────────────────────
        st.markdown("##### 📡 MARKET PULSE")

        # State badge
        st.markdown(f"""
        <div style="
            background: {state_color}15; border: 1px solid {state_color}40;
            border-radius: 8px; padding: 10px 14px; margin: 8px 0 12px;
            text-align: center;
        ">
            <span style="font-size: 20px; font-weight: 700; color: {state_color};">
                {state_emoji} {market_state.upper().replace('_', ' ')}
            </span>
        </div>
        """, unsafe_allow_html=True)

        fg = market_metrics.get('fear_greed', 50)
        rsi = market_metrics.get('rsi', 50)
        vol = market_metrics.get('volatility', 'Medium')

        st.markdown(f"""
        <div style="margin-bottom: 4px;">
            <span style="color: #A0A0A0; font-size: 13px;">Fear & Greed:</span>
            <span style="color: white; font-weight: 600; font-size: 14px;"> {fg}/100</span>
        </div>
        <div style="
            background: #1A1A1A; height: 6px; border-radius: 3px; margin: 6px 0 12px;
            overflow: hidden;
        ">
            <div style="
                background: {'#FF4444' if fg < 30 else '#FFB800' if fg < 55 else '#00FF94'};
                height: 100%; width: {fg}%; border-radius: 3px;
            "></div>
        </div>
        <div style="margin-bottom: 8px;">
            <span style="color: #A0A0A0; font-size: 13px;">BTC RSI:</span>
            <span style="color: white; font-weight: 600;"> {rsi}</span>
        </div>
        <div style="margin-bottom: 8px;">
            <span style="color: #A0A0A0; font-size: 13px;">Volatility:</span>
            <span style="color: white; font-weight: 600;"> {vol}</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # ── Your Profile ─────────────────────────────────────────
        st.markdown("##### 👤 YOUR PROFILE")

        # Risk score visual bar
        risk_blocks = ""
        for i in range(1, 6):
            color = '#00FF94' if i <= risk_score else '#1A1A1A'
            risk_blocks += f'<div style="flex:1; height:8px; background:{color}; border-radius:2px;"></div>'

        st.markdown(f"""
        <div style="margin: 8px 0;">
            <span style="color: #A0A0A0; font-size: 13px;">Risk Score:</span>
            <span style="color: #00FF94; font-weight: 700;"> {risk_score}/5</span>
            <div style="display: flex; gap: 4px; margin-top: 6px;">{risk_blocks}</div>
        </div>
        <div style="margin: 8px 0;">
            <span style="color: #A0A0A0; font-size: 13px;">Type:</span>
            <span style="color: white; font-weight: 600;"> {risk_label} Investor</span>
        </div>
        <div style="margin: 8px 0 16px;">
            <span style="color: #A0A0A0; font-size: 13px;">Source:</span>
            <span style="color: white; font-weight: 600;"> {'Quiz' if entry_method == 'quiz' else 'Portfolio Import'}</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # ── Actions ──────────────────────────────────────────────
        if st.button("🔄 Retake Quiz", key="sidebar_retake", use_container_width=True):
            # Reset quiz state
            st.session_state['quiz_answers'] = {}
            st.session_state['quiz_current_q'] = 0
            st.session_state['quiz_complete'] = False
            st.session_state['recommendations'] = []
            st.session_state['current_page'] = 'quiz'
            st.rerun()

        # ── Export CSV ───────────────────────────────────────────
        csv_buffer = io.StringIO()
        writer = csv.DictWriter(csv_buffer, fieldnames=[
            'rank', 'symbol', 'name', 'weight', 'confidence', 'tier', 'explanation'
        ])
        writer.writeheader()
        for rec in recs:
            writer.writerow({
                'rank': rec['rank'],
                'symbol': rec['symbol'],
                'name': rec['name'],
                'weight': f"{rec['weight']}%",
                'confidence': f"{rec['confidence']}%",
                'tier': rec['tier'],
                'explanation': rec['explanation'],
            })

        st.download_button(
            "📥 Export Results (CSV)",
            data=csv_buffer.getvalue(),
            file_name="portfoliopulse_portfolio.csv",
            mime="text/csv",
            use_container_width=True,
        )

        # ── Refresh Market Data ──────────────────────────────────
        if st.button("🔄 Refresh Market Data", key="refresh_market", use_container_width=True):
            st.cache_data.clear()
            market = get_market_state()
            st.session_state['market_state'] = market['market_state']
            st.session_state['market_metrics'] = market['market_metrics']
            # Re-run optimization with new market state
            user_idx = st.session_state.get('proxy_user_idx', 0)
            raw_recs = get_neumf_recommendations(user_idx)
            coin_syms = {idx: get_coin_symbol(idx) for idx, _ in raw_recs}
            optimized = optimize_portfolio(raw_recs, market['market_state'], risk_score, coin_syms)
            st.session_state['regime_explanation'] = optimized['regime_explanation']
            enriched = enrich_recommendations(optimized['allocations'], market['market_state'])
            st.session_state['recommendations'] = enriched
            st.rerun()

    # ═══════════════════════════════════════════════════════════════
    # MAIN AREA
    # ═══════════════════════════════════════════════════════════════

    # ── A) Hero Stats Row ────────────────────────────────────────
    avg_confidence = sum(r['confidence'] for r in recs) / len(recs) if recs else 0

    stat_card = """
        background: #111111; border: 1px solid #222222;
        border-radius: 12px; padding: 20px; text-align: center;
    """

    sc1, sc2, sc3, sc4 = st.columns(4)

    with sc1:
        st.markdown(f"""
        <div style="{stat_card}">
            <div style="color: #A0A0A0; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">
                Market State
            </div>
            <div style="font-size: 24px; margin-bottom: 4px;">{state_emoji}</div>
            <div style="
                display: inline-block; background: {state_color}20;
                border: 1px solid {state_color}40; border-radius: 6px;
                padding: 4px 12px; color: {state_color}; font-weight: 700;
                font-size: 13px;
            ">{market_state.upper().replace('_', ' ')}</div>
        </div>
        """, unsafe_allow_html=True)

    with sc2:
        st.markdown(f"""
        <div style="{stat_card}">
            <div style="color: #A0A0A0; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">
                Tokens Found
            </div>
            <div style="color: #00FF94; font-size: 36px; font-weight: 800; font-family: 'JetBrains Mono', monospace;">
                {len(recs)}
            </div>
            <div style="color: #A0A0A0; font-size: 12px;">recommended</div>
        </div>
        """, unsafe_allow_html=True)

    with sc3:
        st.markdown(f"""
        <div style="{stat_card}">
            <div style="color: #A0A0A0; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">
                Risk Score
            </div>
            <div style="color: #00FF94; font-size: 36px; font-weight: 800; font-family: 'JetBrains Mono', monospace;">
                {risk_score} / 5
            </div>
            <div style="color: #A0A0A0; font-size: 12px;">{risk_label}</div>
        </div>
        """, unsafe_allow_html=True)

    with sc4:
        conf_color = '#00FF94' if avg_confidence > 60 else '#FFB800' if avg_confidence > 40 else '#A0A0A0'
        conf_label = 'High Signal' if avg_confidence > 60 else 'Moderate' if avg_confidence > 40 else 'Exploratory'
        st.markdown(f"""
        <div style="{stat_card}">
            <div style="color: #A0A0A0; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">
                Confidence
            </div>
            <div style="color: {conf_color}; font-size: 36px; font-weight: 800; font-family: 'JetBrains Mono', monospace;">
                {int(avg_confidence)}%
            </div>
            <div style="color: #A0A0A0; font-size: 12px;">{conf_label}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # ── B) Regime Alert Banner ───────────────────────────────────
    regime_msg = get_regime_message(market_state)
    banner_bg = {
        'bull': '#003D2130',
        'bear': '#FF444420',
        'extreme_fear': '#FF444425',
        'neutral': '#FFB80015',
        'high_volatility': '#FFB80020',
    }.get(market_state, '#1A1A1A')
    banner_border = f"{state_color}40"

    st.markdown(f"""
    <div style="
        background: {banner_bg}; border: 1px solid {banner_border};
        border-radius: 12px; padding: 16px 24px; margin-bottom: 24px;
    ">
        <p style="color: white; font-size: 15px; font-weight: 600; margin: 0;">
            {regime_msg}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── C) Two-column layout (60/40) ────────────────────────────
    col_left, col_right = st.columns([3, 2], gap="large")

    # ── LEFT: Recommendation Cards ───────────────────────────────
    with col_left:
        st.markdown(f"""
        <div style="margin-bottom: 20px;">
            <h2 style="color: white; font-size: 24px; font-weight: 700; margin-bottom: 4px;">
                Your Personalized Portfolio
            </h2>
            <p style="color: #A0A0A0; font-size: 14px;">
                Based on {market_state.replace('_', ' ').upper()} conditions + your {risk_label} risk profile
            </p>
        </div>
        """, unsafe_allow_html=True)

        for rec in recs:
            # Tier badge styling
            tier_colors = {
                'High Signal': ('#00FF94', '#003D21'),
                'Moderate':    ('#FFB800', '#3D2E00'),
                'Exploratory': ('#A0A0A0', '#1A1A1A'),
            }
            tc, tbg = tier_colors.get(rec['tier'], ('#A0A0A0', '#1A1A1A'))

            # Confidence bar
            conf = rec['confidence']
            conf_bar_filled = int(conf / 10)
            conf_bar = '█' * conf_bar_filled + '░' * (10 - conf_bar_filled)

            # Logo — use img tag or fallback initial
            logo_url = rec.get('logo_url', '')
            if logo_url:
                logo_html = f'<img src="{logo_url}" width="36" height="36" style="border-radius:50%;background:#1A1A1A;">'
            else:
                logo_html = f'<span style="display:inline-block;width:36px;height:36px;border-radius:50%;background:#1A1A1A;line-height:36px;text-align:center;color:#00FF94;font-weight:700;font-size:14px;">{rec["symbol"][:2]}</span>'

            card_html = f"""<div style="background:#111111;border:1px solid #222222;border-radius:12px;padding:20px;margin-bottom:12px;">
<table style="width:100%;border:none;border-collapse:collapse;"><tr style="border:none;">
<td style="border:none;width:30px;vertical-align:top;color:#00C46A;font-size:15px;font-weight:700;padding-right:8px;">#{rec['rank']}</td>
<td style="border:none;width:40px;vertical-align:top;padding-right:12px;">{logo_html}</td>
<td style="border:none;vertical-align:top;">
<span style="color:white;font-size:16px;font-weight:700;">{rec['name']}</span>
<span style="color:#A0A0A0;font-weight:400;margin-left:6px;">{rec['symbol']}</span>
<br><span style="color:#A0A0A0;font-size:12px;">{rec['explanation']}</span>
</td>
<td style="border:none;text-align:right;vertical-align:top;">
<span style="color:#00FF94;font-size:24px;font-weight:800;font-family:'JetBrains Mono',monospace;">{rec['weight']}%</span>
</td>
</tr></table>
<div style="background:#1A1A1A;height:4px;border-radius:2px;margin:12px 0 8px;overflow:hidden;">
<div style="background:linear-gradient(90deg,#00FF94,#00C46A);height:100%;width:{rec['weight']}%;border-radius:2px;"></div></div>
<table style="width:100%;border:none;border-collapse:collapse;"><tr style="border:none;">
<td style="border:none;"><span style="color:{tc};font-family:'JetBrains Mono',monospace;font-size:12px;letter-spacing:1px;">{conf_bar}</span> <span style="color:#A0A0A0;font-size:12px;">{conf}%</span></td>
<td style="border:none;text-align:right;"><span style="background:{tbg};color:{tc};font-size:11px;font-weight:600;padding:3px 10px;border-radius:6px;border:1px solid {tc}30;">{rec['tier']}</span></td>
</tr></table>
</div>"""

            st.markdown(card_html, unsafe_allow_html=True)

    # ── RIGHT: Donut Chart ───────────────────────────────────────
    with col_right:
        st.markdown("""
        <h3 style="color: white; font-size: 18px; font-weight: 700; margin-bottom: 16px;">
            Portfolio Allocation
        </h3>
        """, unsafe_allow_html=True)

        # Build donut chart
        labels = [r['symbol'] for r in recs]
        values = [r['weight'] for r in recs]

        # Green gradient palette
        n = len(recs)
        colors_palette = []
        for i in range(n):
            r_val = int(0 + (0 - 0) * i / max(n - 1, 1))
            g_val = int(255 - (255 - 61) * i / max(n - 1, 1))
            b_val = int(148 - (148 - 33) * i / max(n - 1, 1))
            colors_palette.append(f'rgb({r_val},{g_val},{b_val})')

        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.65,
            marker=dict(colors=colors_palette, line=dict(color='#0A0A0A', width=2)),
            textinfo='none',
            hovertemplate='<b>%{label}</b><br>%{value:.1f}%<extra></extra>',
        )])

        fig.update_layout(
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=20, b=20),
            height=300,
            annotations=[dict(
                text="PORTFOLIO<br>ALLOCATION",
                x=0.5, y=0.5, font_size=13, font_color='#A0A0A0',
                showarrow=False, font=dict(family='Inter'),
            )],
        )

        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        # ── Custom Legend (Allocation Bars) ──────────────────────
        st.markdown("<div style='margin-top: 8px;'>", unsafe_allow_html=True)
        for i, rec in enumerate(recs):
            bar_width = max(5, rec['weight'])
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                <span style="
                    color: #A0A0A0; font-size: 13px; font-family: 'JetBrains Mono', monospace;
                    min-width: 50px;
                ">{rec['symbol']}</span>
                <div style="flex: 1; background: #1A1A1A; height: 8px; border-radius: 4px; overflow: hidden;">
                    <div style="
                        background: {colors_palette[i] if i < len(colors_palette) else '#00FF94'};
                        height: 100%; width: {bar_width}%;
                        border-radius: 4px;
                    "></div>
                </div>
                <span style="
                    color: white; font-size: 13px; font-weight: 600;
                    font-family: 'JetBrains Mono', monospace; min-width: 45px;
                    text-align: right;
                ">{rec['weight']}%</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)

    # ── D) Explainability Panel ──────────────────────────────────
    st.markdown(f"""
    <div style="
        background: #111111; border: 1px solid #00FF9425;
        border-radius: 12px; padding: 32px; margin-bottom: 32px;
    ">
        <h2 style="color: white; font-size: 22px; font-weight: 700; margin-bottom: 24px;">
            🧠 Why These Recommendations?
        </h2>
    </div>
    """, unsafe_allow_html=True)

    ex1, ex2, ex3 = st.columns(3)

    explain_card = """
        background: #111111; border: 1px solid #222222;
        border-radius: 12px; padding: 24px; height: 100%;
    """

    # Smart money column
    top_coins = ', '.join([r['symbol'] for r in recs[:3]])
    proxy_pool = st.session_state.get('proxy_user_idx', 0)

    with ex1:
        st.markdown(f"""
        <div style="{explain_card}">
            <div style="font-size: 28px; margin-bottom: 12px;">👥</div>
            <h4 style="color: white; font-size: 16px; font-weight: 700; margin-bottom: 8px;">
                What Smart Money Is Doing
            </h4>
            <p style="color: #A0A0A0; font-size: 14px; line-height: 1.6;">
                Our AI found investors with your profile. Top holds: {top_coins}.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with ex2:
        fg = market_metrics.get('fear_greed', 50)
        rsi = market_metrics.get('rsi', 50)
        rsi_status = 'healthy, not overbought' if rsi < 70 else 'overbought — caution' if rsi < 80 else 'extremely overbought'

        st.markdown(f"""
        <div style="{explain_card}">
            <div style="font-size: 28px; margin-bottom: 12px;">📡</div>
            <h4 style="color: white; font-size: 16px; font-weight: 700; margin-bottom: 8px;">
                Market Context
            </h4>
            <p style="color: #A0A0A0; font-size: 14px; line-height: 1.6;">
                {market_state.upper().replace('_', ' ')} mode. RSI={rsi} — {rsi_status}.
                Fear & Greed at {fg}.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with ex3:
        max_cap = {1: 25, 2: 30, 3: 40, 4: 45, 5: 50}.get(risk_score, 40)
        st.markdown(f"""
        <div style="{explain_card}">
            <div style="font-size: 28px; margin-bottom: 12px;">⚖️</div>
            <h4 style="color: white; font-size: 16px; font-weight: 700; margin-bottom: 8px;">
                Your Risk Filter
            </h4>
            <p style="color: #A0A0A0; font-size: 14px; line-height: 1.6;">
                {risk_label} score capped any single asset at {max_cap}% to keep you diversified.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # ── Confidence Legend ────────────────────────────────────────
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    lg1, lg2, lg3 = st.columns(3)
    with lg1:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="color: #00FF94; font-family: 'JetBrains Mono', monospace; font-size: 12px;">████</span>
            <span style="color: #A0A0A0; font-size: 12px;"><b style="color: #00FF94;">High Signal</b> — Many similar investors hold this</span>
        </div>
        """, unsafe_allow_html=True)
    with lg2:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="color: #FFB800; font-family: 'JetBrains Mono', monospace; font-size: 12px;">███░</span>
            <span style="color: #A0A0A0; font-size: 12px;"><b style="color: #FFB800;">Moderate</b> — Pattern exists but less common</span>
        </div>
        """, unsafe_allow_html=True)
    with lg3:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="color: #A0A0A0; font-family: 'JetBrains Mono', monospace; font-size: 12px;">██░░</span>
            <span style="color: #A0A0A0; font-size: 12px;"><b>Exploratory</b> — Emerging pick, limited support</span>
        </div>
        """, unsafe_allow_html=True)
