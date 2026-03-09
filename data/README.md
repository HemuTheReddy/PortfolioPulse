# Placeholder — drop your real data files here:
# - CryptoInteractions.csv
# - coin_manifest.json
# - qualified_wallets.csv
# - contract_overrides.json — manual labels for proxy/special contracts (e.g. Blur Bidding Pool)
#
# Fixing coin_manifest.json (wrong symbols/names, correct contract_address):
#   python scripts/fix_coin_manifest.py --provider auto     # Moralis -> CoinGecko -> onchain (best for obscure tokens)
#   python scripts/fix_coin_manifest.py --provider onchain # reads name/symbol from contract (works for ANY ERC20)
#   python scripts/fix_coin_manifest.py --provider moralis  # needs MORALIS_API_KEY, includes logos
