#!/usr/bin/env python3
"""
Fix coin_manifest.json by fetching correct symbol, name, logo_url from external APIs.

Uses contract_address (which is correct) to look up metadata from:
  1. onchain - reads name()/symbol() directly from contract via eth_call (works for ANY ERC20)
  2. Moralis (MORALIS_API_KEY) - on-chain metadata + logo
  3. CoinGecko (free) - best for popular tokens, includes logo
  4. Covalent (COVALENT_API_KEY) - alternative
  5. auto - try Moralis -> CoinGecko -> onchain (best data first, fallback for obscure tokens)

Usage:
  python scripts/fix_coin_manifest.py [options]

Options:
  --provider onchain|moralis|coingecko|covalent|auto  Provider (default: auto)
  --chain ethereum|polygon|bsc|...       Chain for lookup (default: ethereum)
  --limit N                              Only process first N coins (for testing)
  --skip-good                            Skip coins that already have valid data
  --dry-run                              Don't write changes
  --delay SEC                            Delay between API calls (default: 6 for free tier)
  --progress N                           Save progress every N coins (default: 100)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load .env from project root (dotenv + manual fallback for when dotenv path fails)
def _load_env() -> None:
    env_files = [PROJECT_ROOT / ".env", PROJECT_ROOT / ".env.local"]
    try:
        from dotenv import load_dotenv
        for p in env_files:
            if p.exists():
                load_dotenv(p, override=False)
    except ImportError:
        pass
    # Fallback: manually parse .env (handles dotenv path issues, missing dotenv, etc.)
    for p in env_files:
        if not p.exists():
            continue
        try:
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, _, v = line.partition("=")
                        k, v = k.strip(), v.strip().strip('"').strip("'")
                        if k and v and k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

_load_env()

MANIFEST_PATH = PROJECT_ROOT / "data" / "coin_manifest.json"
OVERRIDES_PATH = PROJECT_ROOT / "data" / "contract_overrides.json"
PROGRESS_PATH = PROJECT_ROOT / "data" / "coin_manifest_fix_progress.json"


def load_contract_overrides() -> dict:
    """Load manual overrides for proxy/special contracts (e.g. Blur Bidding Pool)."""
    if not OVERRIDES_PATH.exists():
        return {}
    try:
        with open(OVERRIDES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {k.lower(): v for k, v in data.items() if k.startswith("0x") and isinstance(v, dict)}
    except Exception:
        return {}


def load_manifest() -> dict:
    """Load coin_manifest.json. Keys are strings like '0', '2', etc."""
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_manifest(manifest: dict) -> None:
    """Save coin_manifest.json with pretty formatting."""
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def looks_like_good_data(entry: dict) -> bool:
    """Return True if symbol/name look valid (skip refresh)."""
    symbol = (entry.get("symbol") or "").strip()
    name = (entry.get("name") or "").strip()
    # Bad: Unknown Token, TKN#, garbled unicode, empty
    if not symbol or not name:
        return False
    if re.match(r"^Unknown Token #\d+$", name, re.I):
        return False
    if re.match(r"^TKN\d+$", symbol, re.I) and len(symbol) <= 6:
        return False
    # Garbled: unicode symbols that look like encoding errors
    if re.search(r"[\ua4f4\ua4e2\ua4d3\u0421]", symbol + name):
        return False
    if len(symbol) > 20 or len(name) > 80:  # Suspiciously long
        return False
    return True


def is_evm_address(addr: str) -> bool:
    return bool(addr and re.match(r"^0x[a-fA-F0-9]{40}$", addr.strip()))


def fetch_coingecko(contract_address: str, chain: str = "ethereum") -> dict | None:
    """Fetch token metadata from CoinGecko. Returns {symbol, name, logo_url, coingecko_id} or None."""
    base = os.getenv("COINGECKO_API_KEY") and "https://pro-api.coingecko.com" or "https://api.coingecko.com"
    url = f"{base}/api/v3/coins/{chain}/contract/{contract_address}"
    headers = {}
    if os.getenv("COINGECKO_API_KEY"):
        headers["x-cg-demo-api-key"] = os.getenv("COINGECKO_API_KEY")
        headers["x-cg-pro-api-key"] = os.getenv("COINGECKO_API_KEY")

    try:
        import requests
        r = requests.get(url, headers=headers or None, timeout=15)
        if r.status_code != 200:
            return None
        data = r.json()
        image = data.get("image") or {}
        logo = image.get("small") or image.get("thumb") or image.get("large")
        return {
            "symbol": (data.get("symbol") or "").upper(),
            "name": data.get("name") or "",
            "logo_url": logo,
            "coingecko_id": data.get("id"),
        }
    except Exception:
        return None


def fetch_moralis(contract_address: str, chain: str = "eth", verbose: bool = False) -> dict | None:
    """Fetch token metadata from Moralis. Returns {symbol, name, logo_url} or None."""
    key = os.getenv("MORALIS_API_KEY")
    if not key:
        return None
    chain_map = {"ethereum": "eth", "polygon": "polygon", "bsc": "bsc", "arbitrum": "arbitrum"}
    chain_id = chain_map.get(chain.lower(), "eth")
    url = f"https://deep-index.moralis.io/api/v2.2/erc20/metadata"
    params = {"chain": chain_id, "addresses": contract_address}
    headers = {"X-API-Key": key}

    try:
        import requests
        r = requests.get(url, params=params, headers=headers, timeout=15)
        if r.status_code != 200:
            if verbose:
                print(f"    Moralis {r.status_code}: {r.text[:200]}")
            return None
        data = r.json()
        if not isinstance(data, list):
            if verbose:
                print(f"    Moralis response not list: {str(data)[:150]}")
            return None
        if not data:
            if verbose:
                print(f"    Moralis empty array for {contract_address[:18]}...")
            return None
        item = data[0] if data else {}
        if not item:
            return None
        logo = item.get("logo") or item.get("thumbnail")
        return {
            "symbol": (item.get("symbol") or "").upper(),
            "name": item.get("name") or "",
            "logo_url": logo,
            "coingecko_id": None,
        }
    except Exception as e:
        if verbose:
            print(f"    Moralis error: {e}")
        return None


def _decode_abi_string(hex_data: str) -> str:
    """Decode ABI-encoded string from eth_call response (dynamic or fixed)."""
    if not hex_data or not hex_data.startswith("0x"):
        return ""
    raw = hex_data[2:]
    if len(raw) < 64:
        return ""
    try:
        # Dynamic encoding: first word is offset to string data
        offset_bytes = int(raw[:64], 16)
        if offset_bytes > 0 and len(raw) >= 128:
            length_pos = offset_bytes * 2
            if length_pos + 64 <= len(raw):
                length = int(raw[length_pos : length_pos + 64], 16)
                if 0 < length <= 500:
                    string_pos = length_pos + 64
                    if string_pos + length * 2 <= len(raw):
                        hex_str = raw[string_pos : string_pos + length * 2]
                        return bytes.fromhex(hex_str).decode("utf-8", errors="replace").strip("\x00")
        # Fixed: short string right-padded in single 32-byte word
        try:
            decoded = bytes.fromhex(raw[:64]).decode("utf-8", errors="replace").strip("\x00")
            if decoded and decoded.isprintable() and len(decoded) <= 32:
                return decoded
        except Exception:
            pass
    except Exception:
        pass
    return ""


def fetch_onchain(contract_address: str, chain: str = "ethereum") -> dict | None:
    """Read name() and symbol() directly from ERC20 contract via eth_call. Works for ANY token."""
    rpc_map = {
        "ethereum": [
            "https://cloudflare-eth.com",
            "https://rpc.ankr.com/eth",
            "https://ethereum.publicnode.com",
            "https://eth.llamarpc.com",
        ],
        "polygon": ["https://polygon-bor-rpc.publicnode.com", "https://polygon.llamarpc.com"],
        "bsc": ["https://bsc-dataseed.binance.org"],
        "arbitrum": ["https://arb1.arbitrum.io/rpc"],
    }
    rpc_list = [os.getenv("ETH_RPC_URL")] if os.getenv("ETH_RPC_URL") else rpc_map.get(chain.lower(), rpc_map["ethereum"])
    addr = contract_address.strip()
    if not is_evm_address(addr):
        return None
    # ERC20 selectors: name()=0x06fdde03, symbol()=0x95d89b41
    payloads = [("name", "0x06fdde03"), ("symbol", "0x95d89b41")]
    result = {}
    rpc_list = [r for r in rpc_list if r]
    try:
        import requests
        for rpc_url in rpc_list:
            for field, selector in payloads:
                if result.get(field):
                    continue
                body = {
                    "jsonrpc": "2.0",
                    "method": "eth_call",
                    "params": [{"to": addr, "data": selector}, "latest"],
                    "id": 1,
                }
                try:
                    r = requests.post(rpc_url, json=body, timeout=12)
                    if r.status_code != 200:
                        continue
                    data = r.json()
                    if data.get("error"):
                        continue
                    hex_result = data.get("result") or ""
                    result[field] = _decode_abi_string(hex_result)
                except Exception:
                    continue
            if result.get("symbol") or result.get("name"):
                break
        if result.get("symbol") or result.get("name"):
            return {
                "symbol": (result.get("symbol") or "").upper(),
                "name": result.get("name") or "",
                "logo_url": None,
                "coingecko_id": None,
            }
    except Exception:
        pass
    return None


def fetch_covalent(contract_address: str, chain: str = "eth-mainnet") -> dict | None:
    """Fetch token metadata from Covalent. Returns {symbol, name, logo_url} or None."""
    key = os.getenv("COVALENT_API_KEY")
    if not key:
        return None
    chain_map = {"ethereum": "eth-mainnet", "polygon": "matic-mainnet", "bsc": "bsc-mainnet"}
    chain_id = chain_map.get(chain.lower(), "eth-mainnet")
    url = f"https://api.covalenthq.com/v1/{chain_id}/tokens/{contract_address}/"
    params = {"key": key}

    try:
        import requests
        r = requests.get(url, params=params, timeout=15)
        if r.status_code != 200:
            return None
        data = r.json()
        item = (data.get("data") or {}).get("items") or []
        if not item:
            return None
        item = item[0]
        contract = item.get("contract_metadata") or {}
        logo = contract.get("logo_url")
        return {
            "symbol": (contract.get("contract_ticker_symbol") or item.get("contract_ticker_symbol") or "").upper(),
            "name": contract.get("contract_name") or item.get("contract_name") or "",
            "logo_url": logo,
            "coingecko_id": None,
        }
    except Exception:
        return None


def fetch_metadata(contract_address: str, provider: str, chain: str, verbose: bool = False) -> dict | None:
    """Fetch metadata using the chosen provider."""
    addr = contract_address.strip()
    if not is_evm_address(addr):
        return None
    if provider == "onchain":
        return fetch_onchain(addr, chain)
    if provider == "coingecko":
        return fetch_coingecko(addr, chain)
    if provider == "moralis":
        return fetch_moralis(addr, chain, verbose)
    if provider == "covalent":
        return fetch_covalent(addr, chain)
    if provider == "auto":
        # Try best data first, fallback to onchain for obscure tokens
        meta = fetch_moralis(addr, chain, verbose)
        if meta and meta.get("symbol") and meta.get("name"):
            return meta
        meta = fetch_coingecko(addr, chain)
        if meta and meta.get("symbol") and meta.get("name"):
            return meta
        return fetch_onchain(addr, chain)
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description="Fix coin_manifest.json using token metadata APIs")
    ap.add_argument("--provider", choices=["onchain", "moralis", "coingecko", "covalent", "auto"], default="auto")
    ap.add_argument("--chain", default="ethereum")
    ap.add_argument("--limit", type=int, default=None, help="Process only first N coins")
    ap.add_argument("--skip-good", action="store_true", help="Skip coins that already look valid")
    ap.add_argument("--dry-run", action="store_true", help="Don't write changes")
    ap.add_argument("--delay", type=float, default=6.0, help="Seconds between API calls")
    ap.add_argument("--progress", type=int, default=100, help="Save progress every N coins")
    ap.add_argument("--verbose", "-v", action="store_true", help="Print API errors for debugging")
    args = ap.parse_args()

    if args.provider == "moralis" and not os.getenv("MORALIS_API_KEY"):
        print("Moralis requires MORALIS_API_KEY in .env")
        sys.exit(1)
    if args.provider == "covalent" and not os.getenv("COVALENT_API_KEY"):
        print("Covalent requires COVALENT_API_KEY in .env")
        sys.exit(1)
    if args.provider == "auto":
        args.delay = min(args.delay, 2.0)  # auto can be faster (onchain has no rate limit)

    manifest = load_manifest()
    overrides = load_contract_overrides()
    keys = sorted(manifest.keys(), key=lambda k: int(k) if k.isdigit() else 0)
    if args.limit:
        keys = keys[: args.limit]

    updated = 0
    skipped = 0
    failed = 0

    for i, key in enumerate(keys):
        entry = manifest[key]
        contract = entry.get("contract_address")
        if not contract or not is_evm_address(contract):
            skipped += 1
            continue
        if args.skip_good and looks_like_good_data(entry):
            skipped += 1
            continue

        # Check for manual override (e.g. Blur Bidding Pool)
        override = overrides.get(contract.strip().lower())
        if override:
            entry["symbol"] = override.get("symbol") or entry.get("symbol", "")
            entry["name"] = override.get("name") or entry.get("name", "")
            if override.get("logo_url"):
                entry["logo_url"] = override["logo_url"]
            updated += 1
            print(f"  [{key}] {entry['symbol']} — {entry['name']} (override)")
            continue

        meta = fetch_metadata(contract, args.provider, args.chain, args.verbose)
        if meta and meta.get("symbol") and meta.get("name"):
            entry["symbol"] = meta["symbol"]
            entry["name"] = meta["name"]
            if meta.get("logo_url"):
                entry["logo_url"] = meta["logo_url"]
            if meta.get("coingecko_id"):
                entry["coingecko_id"] = meta["coingecko_id"]
            updated += 1
            print(f"  [{key}] {entry['symbol']} — {entry['name']}")
        else:
            failed += 1
            if failed <= 5:  # Only log first few failures
                print(f"  [{key}] SKIP (no data for {contract[:18]}...)")

        if (i + 1) % args.progress == 0 and not args.dry_run and updated > 0:
            save_manifest(manifest)
            print(f"  ... saved progress ({i + 1}/{len(keys)})")

        time.sleep(args.delay)

    if not args.dry_run and updated > 0:
        save_manifest(manifest)
        print(f"\nWrote {MANIFEST_PATH}")

    print(f"\nDone: {updated} updated, {skipped} skipped, {failed} failed (no API data)")


if __name__ == "__main__":
    main()
