"""
coin_metadata.py — item_idx → coin metadata mapping + price enrichment.
"""
import os
import json
import time
import logging
import functools
import requests
from backend.config import COIN_MANIFEST_PATH, COINGECKO_URL, PRICE_CACHE_TTL

logger = logging.getLogger(__name__)


# ─── Demo Manifest ──────────────────────────────────────────────────
DEMO_COINS = {
    0: {"symbol": "BTC",   "name": "Bitcoin",           "coingecko_id": "bitcoin",           "logo_url": "https://assets.coingecko.com/coins/images/1/small/bitcoin.png"},
    1: {"symbol": "ETH",   "name": "Ethereum",          "coingecko_id": "ethereum",          "logo_url": "https://assets.coingecko.com/coins/images/279/small/ethereum.png"},
    2: {"symbol": "BNB",   "name": "BNB",               "coingecko_id": "binancecoin",       "logo_url": "https://assets.coingecko.com/coins/images/825/small/bnb-icon2_2x.png"},
    3: {"symbol": "SOL",   "name": "Solana",            "coingecko_id": "solana",            "logo_url": "https://assets.coingecko.com/coins/images/4128/small/solana.png"},
    4: {"symbol": "XRP",   "name": "XRP",               "coingecko_id": "ripple",            "logo_url": "https://assets.coingecko.com/coins/images/44/small/xrp-symbol-white-128.png"},
    5: {"symbol": "ADA",   "name": "Cardano",           "coingecko_id": "cardano",           "logo_url": "https://assets.coingecko.com/coins/images/975/small/cardano.png"},
    6: {"symbol": "AVAX",  "name": "Avalanche",         "coingecko_id": "avalanche-2",       "logo_url": "https://assets.coingecko.com/coins/images/12559/small/Avalanche_Circle_RedWhite_Trans.png"},
    7: {"symbol": "DOGE",  "name": "Dogecoin",          "coingecko_id": "dogecoin",          "logo_url": "https://assets.coingecko.com/coins/images/5/small/dogecoin.png"},
    8: {"symbol": "DOT",   "name": "Polkadot",          "coingecko_id": "polkadot",          "logo_url": "https://assets.coingecko.com/coins/images/12171/small/polkadot.png"},
    9: {"symbol": "MATIC", "name": "Polygon",           "coingecko_id": "matic-network",     "logo_url": "https://assets.coingecko.com/coins/images/4713/small/matic-token-icon.png"},
    10: {"symbol": "LINK", "name": "Chainlink",         "coingecko_id": "chainlink",         "logo_url": "https://assets.coingecko.com/coins/images/877/small/chainlink-new-logo.png"},
    11: {"symbol": "UNI",  "name": "Uniswap",           "coingecko_id": "uniswap",           "logo_url": "https://assets.coingecko.com/coins/images/12504/small/uni.jpg"},
    12: {"symbol": "ATOM", "name": "Cosmos",             "coingecko_id": "cosmos",            "logo_url": "https://assets.coingecko.com/coins/images/1481/small/cosmos_hub.png"},
    13: {"symbol": "LTC",  "name": "Litecoin",          "coingecko_id": "litecoin",          "logo_url": "https://assets.coingecko.com/coins/images/2/small/litecoin.png"},
    14: {"symbol": "FIL",  "name": "Filecoin",          "coingecko_id": "filecoin",          "logo_url": "https://assets.coingecko.com/coins/images/12817/small/filecoin.png"},
    15: {"symbol": "NEAR", "name": "NEAR Protocol",     "coingecko_id": "near",              "logo_url": "https://assets.coingecko.com/coins/images/10365/small/near.jpg"},
    16: {"symbol": "APT",  "name": "Aptos",             "coingecko_id": "aptos",             "logo_url": "https://assets.coingecko.com/coins/images/26455/small/aptos_round.png"},
    17: {"symbol": "ARB",  "name": "Arbitrum",          "coingecko_id": "arbitrum",          "logo_url": "https://assets.coingecko.com/coins/images/16547/small/photo_2023-03-29_21.47.00.jpeg"},
    18: {"symbol": "OP",   "name": "Optimism",          "coingecko_id": "optimism",          "logo_url": "https://assets.coingecko.com/coins/images/25244/small/Optimism.png"},
    19: {"symbol": "USDT", "name": "Tether",            "coingecko_id": "tether",            "logo_url": "https://assets.coingecko.com/coins/images/325/small/Tether.png"},
    20: {"symbol": "USDC", "name": "USD Coin",          "coingecko_id": "usd-coin",          "logo_url": "https://assets.coingecko.com/coins/images/6319/small/usdc.png"},
    21: {"symbol": "AAVE", "name": "Aave",              "coingecko_id": "aave",              "logo_url": "https://assets.coingecko.com/coins/images/12645/small/AAVE.png"},
    22: {"symbol": "MKR",  "name": "Maker",             "coingecko_id": "maker",             "logo_url": "https://assets.coingecko.com/coins/images/1364/small/Mark_Maker.png"},
    23: {"symbol": "GRT",  "name": "The Graph",         "coingecko_id": "the-graph",         "logo_url": "https://assets.coingecko.com/coins/images/13397/small/Graph_Token.png"},
    24: {"symbol": "INJ",  "name": "Injective",         "coingecko_id": "injective-protocol","logo_url": "https://assets.coingecko.com/coins/images/12882/small/Secondary_Symbol.png"},
    25: {"symbol": "RENDER","name": "Render",            "coingecko_id": "render-token",      "logo_url": "https://assets.coingecko.com/coins/images/11636/small/rndr.png"},
    26: {"symbol": "FTM",  "name": "Fantom",            "coingecko_id": "fantom",            "logo_url": "https://assets.coingecko.com/coins/images/4001/small/Fantom_round.png"},
    27: {"symbol": "ALGO", "name": "Algorand",          "coingecko_id": "algorand",          "logo_url": "https://assets.coingecko.com/coins/images/4380/small/download.png"},
    28: {"symbol": "VET",  "name": "VeChain",           "coingecko_id": "vechain",           "logo_url": "https://assets.coingecko.com/coins/images/1167/small/VET_Token_Icon.png"},
    29: {"symbol": "SAND", "name": "The Sandbox",       "coingecko_id": "the-sandbox",       "logo_url": "https://assets.coingecko.com/coins/images/12129/small/sandbox_logo.jpg"},
    30: {"symbol": "MANA", "name": "Decentraland",      "coingecko_id": "decentraland",      "logo_url": "https://assets.coingecko.com/coins/images/878/small/decentraland-mana.png"},
    31: {"symbol": "AXS",  "name": "Axie Infinity",     "coingecko_id": "axie-infinity",     "logo_url": "https://assets.coingecko.com/coins/images/13029/small/axie_infinity_logo.png"},
    32: {"symbol": "CRV",  "name": "Curve DAO",         "coingecko_id": "curve-dao-token",   "logo_url": "https://assets.coingecko.com/coins/images/12124/small/Curve.png"},
    33: {"symbol": "COMP", "name": "Compound",          "coingecko_id": "compound-governance-token","logo_url": "https://assets.coingecko.com/coins/images/10775/small/COMP.png"},
    34: {"symbol": "SNX",  "name": "Synthetix",         "coingecko_id": "havven",            "logo_url": "https://assets.coingecko.com/coins/images/3406/small/SNX.png"},
    35: {"symbol": "SUSHI","name": "SushiSwap",         "coingecko_id": "sushi",             "logo_url": "https://assets.coingecko.com/coins/images/12271/small/512x512_Logo_no_chop.png"},
    36: {"symbol": "1INCH","name": "1inch",             "coingecko_id": "1inch",             "logo_url": "https://assets.coingecko.com/coins/images/13469/small/1inch-token.png"},
    37: {"symbol": "ENS",  "name": "Ethereum Name Service","coingecko_id": "ethereum-name-service","logo_url": "https://assets.coingecko.com/coins/images/19785/small/acatxTm8_400x400.jpg"},
    38: {"symbol": "LDO",  "name": "Lido DAO",          "coingecko_id": "lido-dao",          "logo_url": "https://assets.coingecko.com/coins/images/13573/small/Lido_DAO.png"},
    39: {"symbol": "RPL",  "name": "Rocket Pool",       "coingecko_id": "rocket-pool",       "logo_url": "https://assets.coingecko.com/coins/images/2090/small/rocket_pool_%28RPL%29.png"},
    40: {"symbol": "DAI",  "name": "Dai",               "coingecko_id": "dai",               "logo_url": "https://assets.coingecko.com/coins/images/9956/small/Badge_Dai.png"},
    41: {"symbol": "XLM",  "name": "Stellar",           "coingecko_id": "stellar",           "logo_url": "https://assets.coingecko.com/coins/images/100/small/Stellar_symbol_black_RGB.png"},
    42: {"symbol": "EOS",  "name": "EOS",               "coingecko_id": "eos",               "logo_url": "https://assets.coingecko.com/coins/images/738/small/eos-eos-logo.png"},
    43: {"symbol": "XTZ",  "name": "Tezos",             "coingecko_id": "tezos",             "logo_url": "https://assets.coingecko.com/coins/images/976/small/Tezos-logo.png"},
    44: {"symbol": "THETA","name": "Theta Network",     "coingecko_id": "theta-token",       "logo_url": "https://assets.coingecko.com/coins/images/2538/small/theta-token-logo.png"},
    45: {"symbol": "ICP",  "name": "Internet Computer", "coingecko_id": "internet-computer", "logo_url": "https://assets.coingecko.com/coins/images/14495/small/Internet_Computer_logo.png"},
    46: {"symbol": "HBAR", "name": "Hedera",            "coingecko_id": "hedera-hashgraph",  "logo_url": "https://assets.coingecko.com/coins/images/3688/small/hbar.png"},
    47: {"symbol": "QNT",  "name": "Quant",             "coingecko_id": "quant-network",     "logo_url": "https://assets.coingecko.com/coins/images/3370/small/5ZOu7brX_400x400.jpg"},
    48: {"symbol": "EGLD", "name": "MultiversX",        "coingecko_id": "elrond-erd-2",      "logo_url": "https://assets.coingecko.com/coins/images/12335/small/egld-token-logo.png"},
    49: {"symbol": "SUI",  "name": "Sui",               "coingecko_id": "sui",               "logo_url": "https://assets.coingecko.com/coins/images/26375/small/sui_asset.jpeg"},
}


@functools.lru_cache(maxsize=1)
def load_coin_manifest() -> dict:
    """
    Load coin_manifest.json. Falls back to DEMO_COINS if not found.
    Returns dict with integer keys mapping to coin info dicts.
    """
    if os.path.exists(COIN_MANIFEST_PATH):
        with open(COIN_MANIFEST_PATH, 'r') as f:
            raw = json.load(f)
        return {int(k): v for k, v in raw.items()}

    return dict(DEMO_COINS)


def get_coin_info(item_idx: int) -> dict:
    """Get coin metadata for a single item_idx."""
    manifest = load_coin_manifest()
    if item_idx in manifest:
        return manifest[item_idx]
    return {
        "symbol": f"TKN{item_idx}",
        "name": f"Token #{item_idx}",
        "coingecko_id": None,
        "logo_url": None,
    }


def get_coin_symbol(item_idx: int) -> str:
    """Quick helper to get just the symbol."""
    return get_coin_info(item_idx).get('symbol', f'TKN{item_idx}')


# ─── Price Fetching ──────────────────────────────────────────────────
_price_cache: dict = {}
_price_cache_time: float = 0


def fetch_prices(coingecko_ids: list[str]) -> dict:
    """
    Fetch current USD prices from CoinGecko.
    Returns {coingecko_id: price_usd}.
    Uses in-memory cache with TTL.
    """
    global _price_cache, _price_cache_time

    if time.time() - _price_cache_time < PRICE_CACHE_TTL and _price_cache:
        return _price_cache

    valid_ids = [cid for cid in coingecko_ids if cid]
    if not valid_ids:
        return {}

    try:
        ids_str = ','.join(valid_ids[:50])
        resp = requests.get(
            f"{COINGECKO_URL}/simple/price",
            params={'ids': ids_str, 'vs_currencies': 'usd', 'include_24hr_change': 'true'},
            timeout=10,
        )
        if resp.status_code == 200:
            _price_cache = resp.json()
            _price_cache_time = time.time()
            return _price_cache
    except Exception:
        pass

    return _price_cache


# ─── Demo Prices ─────────────────────────────────────────────────────
DEMO_PRICES = {
    "bitcoin": {"usd": 67542.0, "usd_24h_change": 2.34},
    "ethereum": {"usd": 3521.0, "usd_24h_change": 1.87},
    "binancecoin": {"usd": 598.0, "usd_24h_change": 0.45},
    "solana": {"usd": 178.0, "usd_24h_change": 4.12},
    "ripple": {"usd": 0.62, "usd_24h_change": -0.89},
    "cardano": {"usd": 0.48, "usd_24h_change": 1.23},
    "avalanche-2": {"usd": 38.5, "usd_24h_change": 3.67},
    "dogecoin": {"usd": 0.145, "usd_24h_change": -1.23},
    "polkadot": {"usd": 7.82, "usd_24h_change": 0.98},
    "matic-network": {"usd": 0.89, "usd_24h_change": 2.01},
    "tether": {"usd": 1.0, "usd_24h_change": 0.01},
    "usd-coin": {"usd": 1.0, "usd_24h_change": 0.0},
}


def _load_token_popularity() -> dict[int, int]:
    """Load real token_popularity from CryptoInteractions.csv."""
    from backend.config import INTERACTIONS_PATH
    if not os.path.exists(INTERACTIONS_PATH):
        return {}
    try:
        import pandas as pd
        df = pd.read_csv(INTERACTIONS_PATH, usecols=['item_idx', 'token_popularity'])
        pop = df.groupby('item_idx')['token_popularity'].first().to_dict()
        return {int(k): int(v) for k, v in pop.items()}
    except Exception:
        return {}


@functools.lru_cache(maxsize=1)
def get_token_popularity() -> dict[int, int]:
    return _load_token_popularity()


def _coingecko_url(coingecko_id: str | None, symbol: str) -> str:
    """Build a CoinGecko URL — direct link if ID known, search otherwise."""
    if coingecko_id:
        return f"https://www.coingecko.com/en/coins/{coingecko_id}"
    return f"https://www.coingecko.com/en/search?query={symbol}"


def enrich_recommendations(
    allocations: list[dict],
    market_state: str,
) -> list[dict]:
    """
    Take optimized allocations and enrich with metadata, prices, and explanations.
    Returns the final list ready for UI rendering.
    """
    from backend.inference import generate_explanation

    manifest = load_coin_manifest()
    popularity_map = get_token_popularity()

    cg_ids = []
    for alloc in allocations:
        info = manifest.get(alloc['item_idx'], {})
        cg_id = info.get('coingecko_id')
        if cg_id:
            cg_ids.append(cg_id)

    prices = fetch_prices(cg_ids) if cg_ids else {}
    if not prices:
        prices = DEMO_PRICES

    enriched = []
    for rank, alloc in enumerate(allocations, 1):
        idx = alloc['item_idx']
        info = manifest.get(idx, {
            'symbol': f'TKN{idx}',
            'name': f'Token #{idx}',
            'coingecko_id': None,
            'logo_url': None,
        })

        symbol = info.get('symbol', f'TKN{idx}')
        name = info.get('name', f'Token #{idx}')
        cg_id = info.get('coingecko_id')
        price_data = prices.get(cg_id, {}) if cg_id else {}
        price_usd = price_data.get('usd', None)
        price_change = price_data.get('usd_24h_change', None)

        # Use real token_popularity from interactions CSV
        token_pop = popularity_map.get(idx, max(5, int(alloc['affinity_score'] * 100)))

        expl = generate_explanation(
            item_idx=idx,
            affinity_score=alloc['affinity_score'],
            market_state=market_state,
            token_popularity=token_pop,
            rank=rank,
            weight=alloc['weight'],
            symbol=symbol,
            name=name,
        )

        enriched.append({
            'rank': rank,
            'item_idx': idx,
            'symbol': symbol,
            'name': name,
            'logo_url': info.get('logo_url'),
            'weight': alloc['weight'],
            'confidence': expl['confidence_pct'],
            'tier': expl['tier'],
            'explanation': expl['explanation'],
            'category': expl.get('category', ''),
            'price_usd': price_usd,
            'price_change_24h': price_change,
            'coingecko_url': _coingecko_url(cg_id, symbol),
            'token_popularity': token_pop,
        })

    return enriched

