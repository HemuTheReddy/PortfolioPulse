"""
03_import.py — Portfolio import page (wallet, exchange API, manual entry).
"""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def render():
    # ── Hide sidebar ─────────────────────────────────────────────
    st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none; }
        .block-container { padding-top: 2rem !important; max-width: 780px; }
    </style>
    """, unsafe_allow_html=True)

    # ── Header ───────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align: center; margin-bottom: 32px;">
        <h1 style="color: white; font-size: 36px; font-weight: 700; margin-bottom: 8px;">
            Import Your Portfolio
        </h1>
        <p style="color: #A0A0A0; font-size: 16px;">
            Choose your preferred import method
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Tabs ─────────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["🔗 Wallet Address", "🔑 Exchange API", "✏️ Manual Entry"])

    # ──────────────────────────────────────────────────────────────
    # TAB 1: Wallet Address
    # ──────────────────────────────────────────────────────────────
    with tab1:
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="
            display: flex; gap: 12px; justify-content: center;
            margin-bottom: 20px;
        ">
            <div style="
                background: #111; border: 1px solid #222; border-radius: 8px;
                padding: 8px 16px; display: flex; align-items: center; gap: 6px;
            ">
                <span style="font-size: 14px;">⟠</span>
                <span style="color: #A0A0A0; font-size: 13px;">Ethereum</span>
            </div>
            <div style="
                background: #111; border: 1px solid #222; border-radius: 8px;
                padding: 8px 16px; display: flex; align-items: center; gap: 6px;
            ">
                <span style="font-size: 14px;">🟡</span>
                <span style="color: #A0A0A0; font-size: 13px;">BSC</span>
            </div>
            <div style="
                background: #111; border: 1px solid #222; border-radius: 8px;
                padding: 8px 16px; display: flex; align-items: center; gap: 6px;
            ">
                <span style="font-size: 14px;">🟣</span>
                <span style="color: #A0A0A0; font-size: 13px;">Polygon</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        wallet = st.text_input(
            "Wallet Address",
            placeholder="0x742d35Cc6634C0532925a3b844Bc9e7595f2bD38",
            key="wallet_input",
            help="Paste your wallet address (ETH, BSC, or Polygon)",
        )

        if st.button("Analyze Wallet →", key="analyze_wallet", type="primary", use_container_width=True):
            if wallet and len(wallet) > 10:
                st.session_state['wallet_address'] = wallet
                st.session_state['import_method'] = 'wallet'
                _process_import([
                    {'symbol': 'ETH', 'amount': 2.5},
                    {'symbol': 'BTC', 'amount': 0.15},
                    {'symbol': 'LINK', 'amount': 150},
                    {'symbol': 'UNI', 'amount': 75},
                    {'symbol': 'AAVE', 'amount': 12},
                    {'symbol': 'SOL', 'amount': 25},
                ])
            else:
                st.error("Please enter a valid wallet address.")

    # ──────────────────────────────────────────────────────────────
    # TAB 2: Exchange API
    # ──────────────────────────────────────────────────────────────
    with tab2:
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        exchange = st.selectbox(
            "Select Exchange",
            ["Coinbase", "Binance", "Kraken", "Other"],
            key="exchange_select",
        )

        api_key = st.text_input("API Key", type="password", key="api_key_input")
        api_secret = st.text_input("API Secret", type="password", key="api_secret_input")

        st.markdown("""
        <div style="
            background: #003D2120; border: 1px solid #00FF9420;
            border-radius: 8px; padding: 12px 16px; margin: 12px 0;
        ">
            <p style="color: #00FF94; font-size: 13px; margin: 0;">
                🔒 Read-only access only. We never trade on your behalf.
            </p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Connect Exchange →", key="connect_exchange", type="primary", use_container_width=True):
            if api_key and api_secret:
                st.session_state['import_method'] = 'api'
                # Simulated exchange holdings
                _process_import([
                    {'symbol': 'BTC', 'amount': 0.5},
                    {'symbol': 'ETH', 'amount': 5.0},
                    {'symbol': 'SOL', 'amount': 50},
                    {'symbol': 'DOT', 'amount': 200},
                    {'symbol': 'AVAX', 'amount': 30},
                ])
            else:
                st.error("Please enter both API Key and API Secret.")

    # ──────────────────────────────────────────────────────────────
    # TAB 3: Manual Entry
    # ──────────────────────────────────────────────────────────────
    with tab3:
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        if 'manual_coins' not in st.session_state:
            st.session_state['manual_coins'] = [{'symbol': '', 'amount': 0.0}]

        coins_list = st.session_state['manual_coins']

        # Available coins for dropdown
        coin_options = [
            'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'AVAX', 'DOGE',
            'DOT', 'MATIC', 'LINK', 'UNI', 'ATOM', 'LTC', 'FIL', 'NEAR',
            'APT', 'ARB', 'OP', 'AAVE', 'MKR', 'GRT', 'INJ', 'RENDER',
            'FTM', 'ALGO', 'VET', 'SAND', 'MANA', 'AXS', 'SUI',
        ]

        for i, coin in enumerate(coins_list):
            col_sym, col_amt, col_del = st.columns([3, 2, 1])
            with col_sym:
                selected = st.selectbox(
                    f"Coin #{i+1}",
                    options=[''] + coin_options,
                    key=f"manual_sym_{i}",
                    index=0 if not coin['symbol'] else (
                        coin_options.index(coin['symbol']) + 1 if coin['symbol'] in coin_options else 0
                    ),
                    label_visibility="collapsed" if i > 0 else "visible",
                )
                coins_list[i]['symbol'] = selected

            with col_amt:
                amt = st.number_input(
                    f"Amount #{i+1}",
                    min_value=0.0,
                    value=coin['amount'],
                    key=f"manual_amt_{i}",
                    label_visibility="collapsed" if i > 0 else "visible",
                )
                coins_list[i]['amount'] = amt

            with col_del:
                if i > 0:
                    if st.button("✕", key=f"manual_del_{i}"):
                        coins_list.pop(i)
                        st.rerun()

        col_add, col_calc = st.columns([1, 1])
        with col_add:
            if st.button("+ Add Another Coin", key="add_coin"):
                coins_list.append({'symbol': '', 'amount': 0.0})
                st.rerun()

        with col_calc:
            valid_coins = [c for c in coins_list if c['symbol'] and c['amount'] > 0]
            if st.button(
                "Calculate My Profile →",
                key="calc_profile",
                type="primary",
                disabled=len(valid_coins) < 1,
            ):
                st.session_state['import_method'] = 'manual'
                _process_import(valid_coins)

    # ── Back button ──────────────────────────────────────────────
    st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)
    if st.button("← Back", key="import_back"):
        st.session_state['current_page'] = 'onboarding'
        st.rerun()


def _process_import(holdings: list[dict]):
    """Process imported holdings through the full backend pipeline."""
    from backend.profile_builder import analyze_holdings, get_risk_label
    from backend.market_state import get_market_state
    from backend.inference import get_neumf_recommendations
    from backend.optimization import optimize_portfolio
    from backend.coin_metadata import enrich_recommendations, get_coin_symbol

    # ── Processing animation ─────────────────────────────────────
    progress_placeholder = st.empty()
    steps = [
        ("✓ Data fetched", 0.2),
        ("⟳ Mapping to AI model tokens...", 0.4),
        ("⟳ Building risk profile...", 0.6),
        ("⟳ Generating recommendations...", 0.8),
    ]

    import time as _time

    for step_text, prog in steps:
        progress_placeholder.markdown(f"""
        <div style="text-align: center; padding: 40px 0;">
            <div style="
                width: 48px; height: 48px; border: 3px solid #222;
                border-top: 3px solid #00FF94; border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 20px;
            "></div>
            <style>@keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}</style>
            <h3 style="color: white; margin-bottom: 8px;">Analyzing your portfolio...</h3>
            <p style="color: #00FF94; font-size: 14px;">{step_text}</p>
        </div>
        """, unsafe_allow_html=True)
        _time.sleep(0.5)

    # ── Run pipeline ─────────────────────────────────────────────
    result = analyze_holdings(holdings)
    risk_score = result.get('risk_score', 3)
    risk_label = get_risk_label(risk_score)

    st.session_state['risk_score'] = risk_score
    st.session_state['risk_label'] = risk_label
    st.session_state['proxy_user_idx'] = result['user_idx']

    market = get_market_state()
    st.session_state['market_state'] = market['market_state']
    st.session_state['market_metrics'] = market['market_metrics']

    raw_recs = get_neumf_recommendations(result['user_idx'])
    coin_symbols = {idx: get_coin_symbol(idx) for idx, _ in raw_recs}
    optimized = optimize_portfolio(raw_recs, market['market_state'], risk_score, coin_symbols)
    st.session_state['regime_explanation'] = optimized['regime_explanation']

    enriched = enrich_recommendations(optimized['allocations'], market['market_state'])
    st.session_state['recommendations'] = enriched
    st.session_state['entry_method'] = 'import'
    st.session_state['results_generated_at'] = _time.strftime('%Y-%m-%d %H:%M:%S')

    progress_placeholder.empty()

    # ── Profile Summary (brief) ──────────────────────────────────
    st.markdown(f"""
    <div style="
        background: #111; border: 1px solid #222; border-radius: 12px;
        padding: 32px; text-align: center; margin: 20px 0;
    ">
        <h3 style="color: white; margin-bottom: 20px;">Here's what we found:</h3>
        <div style="display: flex; justify-content: center; gap: 32px; flex-wrap: wrap;">
            <div>
                <div style="color: #00FF94; font-size: 28px; font-weight: 700;">
                    {len(holdings)}
                </div>
                <div style="color: #A0A0A0; font-size: 13px;">Tokens Held</div>
            </div>
            <div>
                <div style="color: #00FF94; font-size: 28px; font-weight: 700;">
                    ~{result.get('avg_hold_days', 30)} days
                </div>
                <div style="color: #A0A0A0; font-size: 13px;">Avg Hold</div>
            </div>
            <div>
                <div style="color: #00FF94; font-size: 28px; font-weight: 700;">
                    {risk_score}/5
                </div>
                <div style="color: #A0A0A0; font-size: 13px;">Risk — {risk_label}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Get My Recommendations →", key="get_recs", type="primary", use_container_width=True):
        st.session_state['current_page'] = 'results'
        st.rerun()
