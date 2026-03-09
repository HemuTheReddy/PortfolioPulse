"""
profile_builder.py — Quiz/Import → Risk Score → Proxy User Index
"""
import os
import pandas as pd
import numpy as np
from backend.config import WALLETS_PATH, NUM_USERS

# ─── Quiz Scoring Weights ───────────────────────────────────────────
WEIGHTS = {
    'horizon':    {'<1m': 1, '1-6m': 2, '6m-2y': 3, '2y+': 5},
    'loss':       {'sell_all': 1, 'sell_some': 2, 'hold': 3, 'buy_more': 5},
    'experience': {'never': 1, '<1y': 2, '1-3y': 3, '3y+': 5},
    'volatility': {'very_uncomfortable': 1, 'somewhat': 2, 'neutral': 3, 'comfortable': 5},
    'capital':    {'<5pct': 5, '5-15': 4, '15-30': 2, '30plus': 1},
    'goal':       {'preserve': 1, 'steady': 2, 'aggressive': 4, 'speculation': 5},
}

RISK_LABELS = {
    1: "Conservative",
    2: "Moderately Conservative",
    3: "Moderate",
    4: "Moderately Aggressive",
    5: "Aggressive",
}


def calculate_risk_score(answers: dict) -> int:
    """
    Takes quiz answers dict {question_key: answer_key} and returns integer 1-5.
    """
    scores = []
    for q_key, answer in answers.items():
        if q_key in WEIGHTS and answer in WEIGHTS[q_key]:
            scores.append(WEIGHTS[q_key][answer])
    if not scores:
        return 3  # default moderate
    return max(1, min(5, round(np.mean(scores))))


def get_risk_label(risk_score: int) -> str:
    return RISK_LABELS.get(risk_score, "Moderate")


def load_qualified_wallets() -> pd.DataFrame:
    """
    Load qualified_wallets.csv. If not found, generate synthetic data.
    Normalizes schema so risk_tier, avg_hold_days, and token_diversity
    always exist regardless of the source CSV's column names.
    """
    if os.path.exists(WALLETS_PATH):
        df = pd.read_csv(WALLETS_PATH)

        # ── Ensure user_idx exists ───────────────────────────────
        if 'user_idx' not in df.columns:
            df['user_idx'] = df.index

        # ── Derive avg_hold_days if missing ──────────────────────
        if 'avg_hold_days' not in df.columns:
            for alt in ['hold_days', 'avg_hold', 'hold_period']:
                if alt in df.columns:
                    df['avg_hold_days'] = df[alt]
                    break
            else:
                df['avg_hold_days'] = 30

        # ── Derive token_diversity if missing ────────────────────
        if 'token_diversity' not in df.columns:
            for alt in ['diversity', 'num_tokens', 'token_count', 'n_tokens']:
                if alt in df.columns:
                    df['token_diversity'] = df[alt]
                    break
            else:
                df['token_diversity'] = 10

        # ── Derive risk_tier if missing ──────────────────────────
        if 'risk_tier' not in df.columns:
            if 'risk_score' in df.columns:
                df['risk_tier'] = df['risk_score'].apply(
                    lambda s: 'conservative' if s <= 2
                    else 'moderate' if s == 3
                    else 'aggressive'
                )
            else:
                conditions = [
                    (df['avg_hold_days'] > 60) & (df['token_diversity'] < 8),
                    (df['avg_hold_days'].between(20, 60)) & (df['token_diversity'].between(8, 15)),
                ]
                df['risk_tier'] = np.select(conditions, ['conservative', 'moderate'],
                                            default='aggressive')
        return df

    # ── Synthetic fallback ───────────────────────────────────────
    np.random.seed(42)
    n = NUM_USERS
    avg_hold_days = np.random.exponential(40, n).clip(1, 365).astype(int)
    token_diversity = np.random.poisson(10, n).clip(1, 50)

    df = pd.DataFrame({
        'user_idx': list(range(n)),
        'avg_hold_days': avg_hold_days,
        'token_diversity': token_diversity,
    })

    conditions = [
        (df['avg_hold_days'] > 60) & (df['token_diversity'] < 8),
        (df['avg_hold_days'].between(20, 60)) & (df['token_diversity'].between(8, 15)),
    ]
    df['risk_tier'] = np.select(conditions, ['conservative', 'moderate'], default='aggressive')
    return df


def find_nearest_user(risk_score: int) -> dict:
    """
    Cold-start: find closest proxy wallet from training set.
    Returns dict with user_idx and match details.
    """
    df = load_qualified_wallets()

    # Map risk score to tier filter
    if risk_score <= 2:
        tier = 'conservative'
        candidates = df[df['risk_tier'] == 'conservative']
    elif risk_score == 3:
        tier = 'moderate'
        candidates = df[df['risk_tier'] == 'moderate']
    else:
        tier = 'aggressive'
        candidates = df[df['risk_tier'] == 'aggressive']

    # Fall back to full dataset if no matches
    if candidates.empty:
        candidates = df

    # Pick a representative user (median by hold days)
    candidates_sorted = candidates.sort_values('avg_hold_days')
    mid = len(candidates_sorted) // 2
    match = candidates_sorted.iloc[mid]

    return {
        'user_idx': int(match['user_idx']),
        'avg_hold_days': int(match['avg_hold_days']),
        'token_diversity': int(match['token_diversity']),
        'risk_tier': tier,
        'pool_size': len(candidates),
    }


def analyze_holdings(holdings: list[dict]) -> dict:
    """
    Takes a list of holdings [{symbol, amount}] from import flow.
    Determines risk profile from the portfolio characteristics.
    Returns same structure as find_nearest_user.
    """
    n_tokens = len(holdings)  # proxy for token_diversity

    # Simple heuristic: more tokens → more aggressive
    if n_tokens <= 3:
        risk_score = 2
    elif n_tokens <= 8:
        risk_score = 3
    else:
        risk_score = 4

    result = find_nearest_user(risk_score)
    result['detected_tokens'] = n_tokens
    result['risk_score'] = risk_score
    return result
