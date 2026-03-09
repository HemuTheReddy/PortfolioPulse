"""
market_state.py — DynamoDB market state pull with mock fallback.
"""
import random
import time
import logging
from cachetools import TTLCache
from backend.config import AWS_REGION, DYNAMO_TABLE, MARKET_CACHE_TTL

logger = logging.getLogger(__name__)

# TTL cache — stores one entry for MARKET_CACHE_TTL seconds
_market_cache = TTLCache(maxsize=1, ttl=MARKET_CACHE_TTL)
_CACHE_KEY = "market_state"


def _mock_market_state() -> dict:
    """Demo fallback when DynamoDB is unavailable."""
    states = ['bull', 'bear', 'neutral', 'extreme_fear']
    weights = [0.35, 0.20, 0.35, 0.10]
    state = random.choices(states, weights=weights, k=1)[0]

    fear_greed = {
        'bull': random.randint(55, 78),
        'bear': random.randint(20, 38),
        'neutral': random.randint(40, 55),
        'extreme_fear': random.randint(5, 20),
    }[state]

    rsi = {
        'bull': random.randint(55, 68),
        'bear': random.randint(28, 42),
        'neutral': random.randint(42, 58),
        'extreme_fear': random.randint(18, 30),
    }[state]

    return {
        'market_state': state,
        'market_metrics': {
            'fear_greed': fear_greed,
            'rsi': rsi,
            'volatility': random.choice(['Low', 'Medium', 'High']),
            'btc_24h': round(random.uniform(-5.0, 8.0), 2),
        },
        'source': 'demo',
        'timestamp': int(time.time()),
    }


def get_market_state() -> dict:
    """
    Pull latest market state from DynamoDB.
    Falls back to mock data if unavailable. Cached via TTLCache.
    """
    if _CACHE_KEY in _market_cache:
        return _market_cache[_CACHE_KEY]

    try:
        import boto3
        dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
        table = dynamodb.Table(DYNAMO_TABLE)
        response = table.get_item(Key={'MarketID': 'LATEST'})

        if 'Item' in response:
            item = response['Item']
            result = {
                'market_state': item.get('market_state', 'neutral').lower(),
                'market_metrics': {
                    'fear_greed': int(item.get('fear_greed_index', 50)),
                    'rsi': int(item.get('btc_rsi', 50)),
                    'volatility': item.get('volatility', 'Medium'),
                    'btc_24h': float(item.get('btc_24h_change', 0.0)),
                },
                'source': 'dynamodb',
                'timestamp': int(item.get('timestamp', time.time())),
            }
            _market_cache[_CACHE_KEY] = result
            return result
    except Exception as e:
        logger.warning(f"DynamoDB unavailable: {e}")

    result = _mock_market_state()
    _market_cache[_CACHE_KEY] = result
    return result


def get_regime_message(market_state: str) -> str:
    """Return the banner message for the current market regime."""
    messages = {
        'extreme_fear': "⚠️ EXTREME FEAR — Stablecoin allocation forced to 30% to protect against downside.",
        'bear':         "🐻 BEAR MARKET MODE — Defensively weighted. Position sizes reduced.",
        'bull':         "🐂 BULL MARKET — Growth conditions favored. Allocations weighted toward momentum.",
        'neutral':      "⚖️ NEUTRAL CONDITIONS — Balanced allocation based on your risk profile.",
        'high_volatility': "📈 HIGH VOLATILITY — Diversified with stablecoin buffer.",
    }
    return messages.get(market_state, messages['neutral'])


def get_state_color(market_state: str) -> str:
    colors = {
        'bull': '#00FF94',
        'bear': '#FF4444',
        'neutral': '#FFB800',
        'extreme_fear': '#FF4444',
        'high_volatility': '#FFB800',
    }
    return colors.get(market_state, '#A0A0A0')


def get_state_emoji(market_state: str) -> str:
    emojis = {
        'bull': '🐂',
        'bear': '🐻',
        'neutral': '⚖️',
        'extreme_fear': '⚠️',
        'high_volatility': '📈',
    }
    return emojis.get(market_state, '⚖️')
