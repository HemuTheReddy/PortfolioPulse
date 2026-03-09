"""
optimization.py — Mean-Variance Portfolio Optimization with regime rules + risk constraints.

Integrates pypfopt Efficient Frontier (when price history is available) with
affinity-based fallback weights from NeuMF scores.
"""
import numpy as np
import warnings
warnings.filterwarnings('ignore')

from backend.config import DISPLAY_TOP_N

# ─── Regime Rules ────────────────────────────────────────────────────
# Aligns with DynamoDB market state + project spec
REGIME_RULES = {
    'bull': {
        'stablecoin_floor': 0.0,
        'max_single_asset': 0.40,
        'risk_aversion':    0.5,
        'description': 'Growth conditions — full allocation to momentum assets.',
    },
    'bear': {
        'stablecoin_floor': 0.20,
        'max_single_asset': 0.25,
        'risk_aversion':    2.0,
        'description': 'Defensive mode — reduced position sizes, stablecoin buffer.',
    },
    'extreme_fear': {
        'stablecoin_floor': 0.30,
        'max_single_asset': 0.20,
        'risk_aversion':    3.0,
        'description': 'Capital preservation — forced stablecoin floor of 30%.',
    },
    'neutral': {
        'stablecoin_floor': 0.05,
        'max_single_asset': 0.35,
        'risk_aversion':    1.0,
        'description': 'Balanced allocation with modest stablecoin buffer.',
    },
    'high_volatility': {
        'stablecoin_floor': 0.15,
        'max_single_asset': 0.30,
        'risk_aversion':    1.5,
        'description': 'Diversified allocation with stablecoin buffer.',
    },
}

# ─── Risk Score Constraints ──────────────────────────────────────────
# Each risk level has personal position limits AND a stablecoin floor.
# Constraint merging uses max(regime, personal) for floors and
# min(regime, personal) for caps — always the more conservative.
RISK_SCORE_MAP = {
    1: {'max_single': 0.15, 'stablecoin_floor': 0.40, 'label': 'Conservative'},
    2: {'max_single': 0.20, 'stablecoin_floor': 0.25, 'label': 'Moderately Conservative'},
    3: {'max_single': 0.30, 'stablecoin_floor': 0.10, 'label': 'Moderate'},
    4: {'max_single': 0.35, 'stablecoin_floor': 0.05, 'label': 'Moderately Aggressive'},
    5: {'max_single': 0.40, 'stablecoin_floor': 0.00, 'label': 'Aggressive'},
}

# Known stablecoin symbols
STABLECOIN_SYMBOLS = {'USDT', 'USDC', 'DAI', 'BUSD', 'TUSD', 'FRAX'}


# ═══════════════════════════════════════════════════════════════════════
# CORE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def affinity_based_weights(
    item_indices: list[int],
    affinities: np.ndarray,
    max_single: float,
    temperature: float = 0.3,
) -> dict[int, float]:
    """
    Temperature-scaled softmax of NeuMF affinity scores as portfolio weights.
    Lower temperature → sharper distribution (top picks get more weight).
    Used as primary method when price history is unavailable (cold-start).
    """
    # Scale scores by temperature — lower T amplifies differences
    scaled = affinities / max(temperature, 0.01)
    exp_scores = np.exp(scaled - np.max(scaled))
    weights = exp_scores / exp_scores.sum()

    # Ensure minimum spread: top pick ≥ 2× bottom pick
    if len(weights) > 1 and weights.max() < 2 * weights.min():
        # Apply rank-based decay to force differentiation
        n = len(weights)
        rank_decay = np.array([1.0 / (1 + 0.3 * i) for i in range(n)])
        weights = weights * rank_decay
        weights = weights / weights.sum()

    # Cap max single asset
    weights = np.minimum(weights, max_single)
    weights = weights / weights.sum()  # renormalize

    return dict(zip(item_indices, weights.tolist()))


def apply_stablecoin_floor(
    weights: dict[int, float],
    floor: float,
    stablecoin_indices: list[int],
) -> dict[int, float]:
    """
    Forces minimum stablecoin allocation in bear/fear regimes.
    Scales down non-stablecoin positions proportionally to make room.
    """
    if floor == 0 or not stablecoin_indices:
        return weights

    current_stable = sum(weights.get(i, 0) for i in stablecoin_indices)

    if current_stable >= floor:
        return weights

    # Need to add more stablecoins — reduce other positions proportionally
    deficit = floor - current_stable
    non_stable = {k: v for k, v in weights.items() if k not in stablecoin_indices}
    total_non = sum(non_stable.values())

    if total_non == 0:
        return weights

    # Scale down non-stablecoin positions
    scale = (total_non - deficit) / total_non
    for k in non_stable:
        weights[k] = weights[k] * max(0, scale)

    # Distribute deficit equally among stablecoins
    per_stable = deficit / len(stablecoin_indices)
    for idx in stablecoin_indices:
        weights[idx] = weights.get(idx, 0) + per_stable

    return weights


def get_regime_explanation(market_state: str, stablecoin_floor: float) -> str:
    """
    Generates the plain-English regime explanation for the frontend banner.
    """
    explanations = {
        'extreme_fear': (
            f"⚠️ Extreme Fear detected in the market. "
            f"Forcing {stablecoin_floor*100:.0f}% allocation to stablecoins "
            f"to protect against downside risk."
        ),
        'bear': (
            f"🐻 Bear market conditions detected. "
            f"Reducing risk exposure with {stablecoin_floor*100:.0f}% "
            f"stablecoin floor and lowered position limits."
        ),
        'high_volatility': (
            f"📈 High volatility regime. "
            f"Diversifying positions with {stablecoin_floor*100:.0f}% "
            f"stablecoin buffer."
        ),
        'bull': (
            "🐂 Bull market conditions. "
            "Maximizing growth exposure based on your affinity profile."
        ),
        'neutral': (
            "⚖️ Neutral market conditions. "
            "Balanced allocation based on your risk profile."
        ),
    }
    return explanations.get(market_state, explanations['neutral'])


# ═══════════════════════════════════════════════════════════════════════
# MAIN OPTIMIZATION FUNCTION
# ═══════════════════════════════════════════════════════════════════════

def optimize_portfolio(
    raw_recommendations: list[tuple[int, float]],
    market_state: str,
    risk_score: int,
    coin_symbols: dict[int, str] | None = None,
    price_history=None,
) -> dict:
    """
    Takes NeuMF top picks and applies Mean-Variance Optimization (when price
    history is available) or affinity-based weights (fallback).

    Merges regime rules + personal risk constraints, always choosing the
    more conservative bound.

    Args:
        raw_recommendations: List of (item_idx, affinity_score)
        market_state: Current market regime string
        risk_score: User risk score 1-5
        coin_symbols: Optional mapping {item_idx: symbol} to identify stablecoins
        price_history: Optional DataFrame of historical prices for MVO

    Returns:
        dict with 'allocations' list and 'regime_explanation' string
    """
    if coin_symbols is None:
        coin_symbols = {}

    regime = REGIME_RULES.get(market_state, REGIME_RULES['neutral'])
    risk_config = RISK_SCORE_MAP.get(risk_score, RISK_SCORE_MAP[3])

    # ── Merge constraints (take the more conservative) ───────────
    max_single = min(regime['max_single_asset'], risk_config['max_single'])
    stablecoin_floor = max(regime['stablecoin_floor'], risk_config['stablecoin_floor'])

    # Take top N
    top_n = raw_recommendations[:DISPLAY_TOP_N]
    item_indices = [idx for idx, _ in top_n]
    affinities = np.array([score for _, score in top_n])

    # Identify stablecoin item indices in the recommendations
    stablecoin_indices = [
        idx for idx in item_indices
        if coin_symbols.get(idx, '').upper() in STABLECOIN_SYMBOLS
    ]

    # ── Try Efficient Frontier (pypfopt) if price history exists ─
    weights = None
    if price_history is not None and len(price_history) >= 2:
        try:
            from pypfopt import EfficientFrontier, expected_returns, risk_models

            available_cols = [
                str(i) for i in item_indices
                if str(i) in price_history.columns
            ]

            if len(available_cols) >= 2:
                prices_subset = price_history[available_cols]

                mu = expected_returns.mean_historical_return(prices_subset)
                sigma = risk_models.CovarianceShrinkage(prices_subset).ledoit_wolf()

                ef = EfficientFrontier(mu, sigma, weight_bounds=(0, max_single))
                ef.add_objective(
                    lambda w: regime['risk_aversion'] * (w @ sigma @ w)
                )
                ef.max_sharpe(risk_free_rate=0.02)
                cleaned = ef.clean_weights()

                weights = {int(k): v for k, v in cleaned.items()}
        except Exception:
            weights = None  # fall back to affinity-based

    # ── Fallback: affinity-based weights ─────────────────────────
    if weights is None:
        weights = affinity_based_weights(item_indices, affinities, max_single)

    # ── Apply stablecoin floor ───────────────────────────────────
    weights = apply_stablecoin_floor(weights, stablecoin_floor, stablecoin_indices)

    # ── Normalize to ensure sum = 1.0 ────────────────────────────
    total = sum(weights.values())
    if total > 0:
        weights = {k: v / total for k, v in weights.items() if v > 0.001}
    total = sum(weights.values())
    if total > 0:
        weights = {k: v / total for k, v in weights.items()}

    # ── Build allocations list ───────────────────────────────────
    allocations = []
    for item_idx, weight in weights.items():
        # Find the original affinity score
        aff = next((s for i, s in top_n if i == item_idx), 0.0)
        allocations.append({
            'item_idx': item_idx,
            'weight': round(float(weight) * 100, 1),  # percentage
            'affinity_score': float(aff),
        })

    # Sort by weight descending
    allocations.sort(key=lambda x: x['weight'], reverse=True)

    # ── Build regime explanation ─────────────────────────────────
    explanation = get_regime_explanation(market_state, stablecoin_floor)
    explanation += (
        f" Max single asset capped at {int(max_single*100)}% "
        f"for your {risk_config['label']} profile."
    )

    return {
        'allocations': allocations,
        'regime_explanation': explanation,
    }
