"""
PortfolioPulse — Configuration
All constants, paths, and design tokens.
"""
import os

# ─── Paths ───────────────────────────────────────────────────────────
BASE_DIR           = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH         = os.path.join(BASE_DIR, "models", "neumf_model.keras")
COIN_MANIFEST_PATH = os.path.join(BASE_DIR, "data", "coin_manifest.json")
INTERACTIONS_PATH  = os.path.join(BASE_DIR, "data", "CryptoInteractions.csv")
WALLETS_PATH       = os.path.join(BASE_DIR, "data", "qualified_wallets.csv")
LOGO_PATH          = os.path.join(BASE_DIR, "assets", "logo.svg")

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
ETHERSCAN_API_KEY  = os.getenv("ETHERSCAN_API_KEY", "")
MORALIS_API_KEY    = os.getenv("MORALIS_API_KEY", "")

# ─── Cache TTLs (seconds) ───────────────────────────────────────────
MARKET_CACHE_TTL   = 1800    # 30 min DynamoDB cache
PRICE_CACHE_TTL    = 300     # 5 min CoinGecko cache

# ─── Design System ──────────────────────────────────────────────────
COLORS = {
    "bg_primary":      "#0A0A0A",
    "bg_card":         "#111111",
    "bg_elevated":     "#1A1A1A",
    "accent_green":    "#00FF94",
    "accent_green_m":  "#00C46A",
    "accent_green_d":  "#003D21",
    "text_primary":    "#FFFFFF",
    "text_secondary":  "#A0A0A0",
    "border":          "#222222",
    "border_accent":   "#00FF9430",
    "warning":         "#FFB800",
    "danger":          "#FF4444",
}
