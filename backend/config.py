"""
PortfolioPulse — Configuration
All constants, paths, and design tokens.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ─── Paths ───────────────────────────────────────────────────────────
BASE_DIR           = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH         = os.path.join(BASE_DIR, "models", "neumf_model.keras")
COIN_MANIFEST_PATH = os.path.join(BASE_DIR, "data", "coin_manifest.json")
INTERACTIONS_PATH  = os.path.join(BASE_DIR, "data", "CryptoInteractions.csv")
WALLETS_PATH       = os.path.join(BASE_DIR, "data", "qualified_wallets.csv")

# ─── Model Dimensions ───────────────────────────────────────────────
NUM_USERS          = 4966
NUM_ITEMS          = 3755

# ─── Inference ───────────────────────────────────────────────────────
TOP_N_INFERENCE    = 20      # NeuMF scores all items, returns top 20
DISPLAY_TOP_N      = 10      # Show user top 10

# ─── AWS / DynamoDB ──────────────────────────────────────────────────
AWS_REGION         = os.getenv("AWS_REGION", "us-east-2")
DYNAMO_TABLE       = os.getenv("DYNAMO_TABLE", "MarketState")

# ─── APIs ────────────────────────────────────────────────────────────
COINGECKO_URL      = "https://api.coingecko.com/api/v3"

# ─── Cache TTLs (seconds) ───────────────────────────────────────────
MARKET_CACHE_TTL   = 1800    # 30 min DynamoDB cache
PRICE_CACHE_TTL    = 300     # 5 min CoinGecko cache
