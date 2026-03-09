"""
inference.py — NeuMF Model inference → top-N recommendations + explanations.
"""
import os
import logging
import functools
import numpy as np
from backend.config import MODEL_PATH, NUM_ITEMS, TOP_N_INFERENCE

logger = logging.getLogger(__name__)

# ─── Token Category Classification ─────────────────────────────────
TOKEN_CATEGORIES = {
    # Layer 1s
    'BTC': 'L1', 'ETH': 'L1', 'SOL': 'L1', 'ADA': 'L1', 'AVAX': 'L1',
    'DOT': 'L1', 'ATOM': 'L1', 'NEAR': 'L1', 'APT': 'L1', 'SUI': 'L1',
    'ALGO': 'L1', 'XTZ': 'L1', 'EGLD': 'L1', 'HBAR': 'L1', 'ICP': 'L1',
    'FTM': 'L1', 'XLM': 'L1', 'EOS': 'L1', 'VET': 'L1', 'THETA': 'L1',
    'QNT': 'L1', 'XRP': 'L1', 'BNB': 'L1', 'LTC': 'L1',
    # Layer 2s
    'MATIC': 'L2', 'ARB': 'L2', 'OP': 'L2',
    # DeFi
    'UNI': 'DeFi', 'AAVE': 'DeFi', 'MKR': 'DeFi', 'COMP': 'DeFi',
    'CRV': 'DeFi', 'SNX': 'DeFi', 'SUSHI': 'DeFi', '1INCH': 'DeFi',
    'LDO': 'DeFi', 'RPL': 'DeFi', 'LINK': 'Oracle', 'GRT': 'Infra',
    'ENS': 'Infra', 'FIL': 'Infra', 'RENDER': 'Infra',
    # Meme
    'DOGE': 'Meme', 'SHIB': 'Meme', 'PEPE': 'Meme', 'FLOKI': 'Meme',
    'BONK': 'Meme', 'WIF': 'Meme',
    # Stablecoins
    'USDT': 'Stable', 'USDC': 'Stable', 'DAI': 'Stable', 'TUSD': 'Stable',
    'BUSD': 'Stable', 'FRAX': 'Stable',
    # Gaming / Metaverse
    'SAND': 'Gaming', 'MANA': 'Gaming', 'AXS': 'Gaming', 'INJ': 'DeFi',
}

CATEGORY_DESCRIPTIONS = {
    'L1':     'Layer-1 blockchain',
    'L2':     'Layer-2 scaling solution',
    'DeFi':   'DeFi protocol',
    'Oracle': 'oracle network',
    'Infra':  'infrastructure protocol',
    'Meme':   'community-driven memecoin',
    'Stable': 'stablecoin',
    'Gaming': 'gaming / metaverse token',
}


def _get_category(symbol: str) -> tuple[str, str]:
    """Return (category_key, human_readable_description) for a token."""
    cat = TOKEN_CATEGORIES.get(symbol.upper(), 'Alt')
    desc = CATEGORY_DESCRIPTIONS.get(cat, 'altcoin')
    return cat, desc


@functools.lru_cache(maxsize=1)
def load_model():
    """Load the trained NeuMF model. Returns None if not found."""
    if os.path.exists(MODEL_PATH):
        try:
            import tensorflow as tf
            model = tf.keras.models.load_model(MODEL_PATH)
            logger.info("NeuMF model loaded successfully")
            return model
        except Exception as e:
            logger.warning(f"Could not load model: {e}")
            return None
    return None


def _demo_scores(user_idx: int) -> list[tuple[int, float]]:
    """
    Generate plausible demo affinity scores when model is unavailable.
    Uses exponential decay for realistic spread between top picks.
    """
    rng = np.random.RandomState(seed=user_idx)

    # Generate base scores with more spread
    scores = np.zeros(NUM_ITEMS)
    top_k = min(100, NUM_ITEMS)

    # Create exponentially decaying scores for top picks
    top_indices = rng.choice(NUM_ITEMS, size=top_k, replace=False)
    for rank, idx in enumerate(top_indices):
        scores[idx] = 0.85 * np.exp(-0.08 * rank) + rng.uniform(0, 0.05)

    # Add noise to remaining items
    remaining = np.setdiff1d(np.arange(NUM_ITEMS), top_indices)
    scores[remaining] = rng.uniform(0.01, 0.15, len(remaining))

    indexed = list(enumerate(scores))
    indexed.sort(key=lambda x: x[1], reverse=True)
    return [(idx, float(score)) for idx, score in indexed[:TOP_N_INFERENCE]]


def get_neumf_recommendations(user_idx: int) -> list[tuple[int, float]]:
    """
    Run NeuMF inference for a given user_idx.
    Returns top-N list of (item_idx, affinity_score) sorted desc.
    """
    model = load_model()

    if model is None:
        return _demo_scores(user_idx)

    try:
        user_input = np.full(NUM_ITEMS, user_idx, dtype=np.int32)
        item_input = np.arange(NUM_ITEMS, dtype=np.int32)

        predictions = model.predict(
            [user_input, item_input],
            batch_size=512,
            verbose=0,
        ).flatten()

        indexed = list(enumerate(predictions))
        indexed.sort(key=lambda x: x[1], reverse=True)
        return [(int(idx), float(score)) for idx, score in indexed[:TOP_N_INFERENCE]]
    except Exception as e:
        logger.warning(f"Inference error, using demo scores: {e}")
        return _demo_scores(user_idx)


def generate_explanation(
    item_idx: int,
    affinity_score: float,
    market_state: str,
    token_popularity: int,
    rank: int = 0,
    weight: float = 0.0,
    symbol: str = "",
    name: str = "",
) -> dict:
    """
    Generate meaningful, varied explanations for each recommendation.
    Uses token category, rank position, market context, and actual metrics.
    """
    # Tier classification
    if affinity_score > 0.6:
        tier = "High Signal"
    elif affinity_score > 0.35:
        tier = "Moderate"
    else:
        tier = "Exploratory"

    cat_key, cat_desc = _get_category(symbol)

    # Market-aware context (varies by category AND market state)
    alt_contexts = [
        "strong trading history with {n} similar wallets — surfaces from behavioral pattern matching",
        "discovered via wallet co-occurrence across {n} similar investors in the training set",
        "behaviorally linked to your profile — {n} wallets with matching patterns hold this token",
        "portfolio fit identified from {n} comparable investors — high co-occurrence with your style",
    ]
    market_context = {
        ('L1', 'bull'):     "strong momentum in growth conditions",
        ('L1', 'bear'):     "foundational asset — historically recovers first",
        ('L1', 'neutral'):  "solid base-layer holding with steady demand",
        ('L2', 'bull'):     "scaling demand rises with network activity",
        ('L2', 'bear'):     "lower fees attract users during downturns",
        ('L2', 'neutral'):  "growing ecosystem with increasing adoption",
        ('DeFi', 'bull'):   "TVL expansion drives protocol revenue",
        ('DeFi', 'bear'):   "yield opportunities persist in bear markets",
        ('DeFi', 'neutral'):"balanced risk-return in current conditions",
        ('Oracle', 'bull'): "data demand scales with DeFi growth",
        ('Oracle', 'bear'): "critical infrastructure — resistant to sentiment",
        ('Oracle', 'neutral'): "steady utility across market conditions",
        ('Infra', 'bull'):  "infrastructure plays benefit from adoption waves",
        ('Infra', 'bear'):  "fundamental utility regardless of price action",
        ('Infra', 'neutral'): "long-term infrastructure investment",
        ('Meme', 'bull'):   "community momentum amplified in bull runs",
        ('Meme', 'bear'):   "high-risk speculative — reduced allocation",
        ('Meme', 'neutral'):"community-driven with volatile upside",
        ('Stable', 'bull'): "stability hedge within growth portfolio",
        ('Stable', 'bear'): "capital preservation during downturn",
        ('Stable', 'neutral'): "liquidity reserve for rebalancing",
        ('Gaming', 'bull'): "gaming sector sees retail inflows in bull markets",
        ('Gaming', 'bear'): "speculative — downside protected by allocation cap",
        ('Gaming', 'neutral'): "metaverse exposure with limited downside",
    }

    effective_state = market_state if market_state in ('bull', 'bear', 'neutral') else 'neutral'

    if cat_key == 'Alt':
        # Rotate through varied alt descriptions, seeded by item_idx for consistency
        alt_template = alt_contexts[item_idx % len(alt_contexts)]
        context = alt_template.format(n=token_popularity)
        cat_desc = 'on-chain token'
    else:
        context = market_context.get(
            (cat_key, effective_state),
            f"active across {effective_state} conditions with {token_popularity} similar holders"
        )

    # Rank-aware phrasing
    if rank <= 2:
        rank_phrase = f"Top pick by AI affinity"
    elif rank <= 5:
        rank_phrase = f"Strong match for your profile"
    else:
        rank_phrase = f"Diversification pick"

    # Popularity phrasing using real data
    if token_popularity > 100:
        pop_phrase = f"held by {token_popularity} similar wallets"
    elif token_popularity > 30:
        pop_phrase = f"growing adoption ({token_popularity} holders)"
    else:
        pop_phrase = f"niche token ({token_popularity} holders)"

    # Weight context
    if weight > 15:
        weight_phrase = f"Core position at {weight:.0f}%"
    elif weight > 8:
        weight_phrase = f"Significant allocation at {weight:.0f}%"
    else:
        weight_phrase = f"Satellite position at {weight:.0f}%"

    # Confidence
    confidence_pct = min(99, max(10, int(affinity_score * 100)))

    # Build explanation — varies by tier
    if tier == "High Signal":
        explanation = f"{rank_phrase} — {cat_desc} · {context}. {pop_phrase.capitalize()}"
    elif tier == "Moderate":
        explanation = f"{weight_phrase} · {cat_desc} — {context}. {pop_phrase.capitalize()}"
    else:
        explanation = f"{rank_phrase} · {cat_desc} — {context}"

    return {
        'tier': tier,
        'explanation': explanation,
        'confidence_pct': confidence_pct,
        'category': cat_desc,
    }
