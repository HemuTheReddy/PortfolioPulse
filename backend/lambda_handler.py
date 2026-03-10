"""
lambda_handler.py — AWS Lambda entry point for PortfolioPulse.

Replaces the FastAPI backend. One Lambda handles all routes via
API Gateway proxy integration ({proxy+}).

Routes:
    GET  /api/health     → health check
    GET  /api/market     → current market state + metrics
    POST /api/quiz       → quiz answers → risk profile + proxy user
    POST /api/recommend  → NeuMF → optimization → enrichment
    POST /api/import     → holdings → risk → full pipeline
"""

import json
import logging
import os
import traceback

from backend.profile_builder import (
    calculate_risk_score,
    get_risk_label,
    find_nearest_user,
    analyze_holdings,
)
from backend.market_state import get_market_state, get_regime_message, get_state_emoji
from backend.inference import get_neumf_recommendations
from backend.optimization import optimize_portfolio
from backend.coin_metadata import enrich_recommendations, get_coin_symbol

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

_amplify_domain = os.getenv("AMPLIFY_DOMAIN")
if _amplify_domain:
    ALLOWED_ORIGINS.append(f"https://{_amplify_domain}")


def _cors_headers(origin: str | None = None) -> dict:
    """Build CORS response headers. Reflects the request origin if allowed."""
    allowed = origin if origin in ALLOWED_ORIGINS else ALLOWED_ORIGINS[0]
    return {
        "Access-Control-Allow-Origin": allowed,
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Allow-Credentials": "true",
    }


def _response(status: int, body: dict, origin: str | None = None) -> dict:
    """API Gateway proxy-integration response envelope."""
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            **_cors_headers(origin),
        },
        "body": json.dumps(body, default=str),
    }


# ─── Route Handlers ──────────────────────────────────────────────────

def _health():
    return {"status": "ok"}


def _market():
    data = get_market_state()
    state = data["market_state"]
    return {
        **data,
        "regime_message": get_regime_message(state),
        "emoji": get_state_emoji(state),
    }


def _quiz(body: dict):
    answers = body.get("answers", {})
    if not answers:
        raise ValueError("Missing 'answers' in request body")

    risk_score = calculate_risk_score(answers)
    risk_label = get_risk_label(risk_score)
    match = find_nearest_user(risk_score)

    return {
        "risk_score": risk_score,
        "risk_label": risk_label,
        "proxy_user": match,
    }


def _recommend(body: dict):
    user_idx = body.get("user_idx")
    risk_score = body.get("risk_score")
    market_state = body.get("market_state")

    if user_idx is None or risk_score is None or market_state is None:
        raise ValueError("Missing required fields: user_idx, risk_score, market_state")

    raw_recs = get_neumf_recommendations(int(user_idx))

    coin_symbols = {}
    for idx, _ in raw_recs:
        coin_symbols[idx] = get_coin_symbol(idx)

    optimized = optimize_portfolio(
        raw_recommendations=raw_recs,
        market_state=market_state,
        risk_score=int(risk_score),
        coin_symbols=coin_symbols,
    )

    enriched = enrich_recommendations(
        allocations=optimized["allocations"],
        market_state=market_state,
    )

    return {
        "recommendations": enriched,
        "regime_explanation": optimized["regime_explanation"],
        "market_state": market_state,
        "risk_score": risk_score,
    }


def _import_portfolio(body: dict):
    holdings = body.get("holdings", [])
    if not holdings:
        raise ValueError("Missing 'holdings' in request body")

    holdings_dicts = [
        {"symbol": h["symbol"], "amount": h["amount"]} for h in holdings
    ]

    result = analyze_holdings(holdings_dicts)
    risk_score = result.get("risk_score", 3)
    risk_label = get_risk_label(risk_score)
    user_idx = result["user_idx"]

    market_data = get_market_state()
    state = market_data["market_state"]

    raw_recs = get_neumf_recommendations(user_idx)
    coin_symbols = {idx: get_coin_symbol(idx) for idx, _ in raw_recs}
    optimized = optimize_portfolio(raw_recs, state, risk_score, coin_symbols)
    enriched = enrich_recommendations(optimized["allocations"], state)

    return {
        "risk_score": risk_score,
        "risk_label": risk_label,
        "proxy_user": result,
        "market": {
            **market_data,
            "regime_message": get_regime_message(state),
            "emoji": get_state_emoji(state),
        },
        "recommendations": enriched,
        "regime_explanation": optimized["regime_explanation"],
    }


# ─── Router ──────────────────────────────────────────────────────────

ROUTES = {
    ("GET",  "/api/health"):    lambda _: _health(),
    ("GET",  "/api/market"):    lambda _: _market(),
    ("POST", "/api/quiz"):      _quiz,
    ("POST", "/api/recommend"): _recommend,
    ("POST", "/api/import"):    _import_portfolio,
}


def handler(event, context):
    """
    Lambda entry point. Expects API Gateway proxy integration events.
    Supports both REST API and HTTP API (v1 / v2 payload formats).
    """
    logger.info("Event: %s", json.dumps(event, default=str)[:2000])

    origin = (event.get("headers") or {}).get("origin") or (
        (event.get("headers") or {}).get("Origin")
    )

    # Handle CORS preflight
    http_method = event.get("httpMethod") or event.get("requestContext", {}).get(
        "http", {}
    ).get("method", "")
    if http_method == "OPTIONS":
        return _response(200, {}, origin)

    # Extract path — support both v1 and v2 payload formats
    path = event.get("path") or event.get("rawPath", "")
    # Strip stage prefix (e.g. /prod/api/health → /api/health)
    if path.count("/") > 2 and not path.startswith("/api"):
        path = "/" + "/".join(path.split("/")[2:])

    body = {}
    raw_body = event.get("body")
    if raw_body:
        try:
            body = json.loads(raw_body) if isinstance(raw_body, str) else raw_body
        except (json.JSONDecodeError, TypeError):
            return _response(400, {"error": "Invalid JSON body"}, origin)

    route_key = (http_method.upper(), path)
    route_fn = ROUTES.get(route_key)

    if route_fn is None:
        logger.warning("No route for %s %s", http_method, path)
        return _response(404, {"error": f"Not found: {http_method} {path}"}, origin)

    try:
        result = route_fn(body)
        return _response(200, result, origin)
    except ValueError as e:
        logger.warning("Validation error: %s", e)
        return _response(400, {"error": str(e)}, origin)
    except Exception as e:
        logger.error("Unhandled error: %s\n%s", e, traceback.format_exc())
        return _response(500, {"error": "Internal server error"}, origin)
