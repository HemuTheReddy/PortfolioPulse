"""
api.py — FastAPI backend for PortfolioPulse.
Wraps all existing backend modules as REST endpoints.
"""
import sys
import os
import logging

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.profile_builder import calculate_risk_score, get_risk_label, find_nearest_user, analyze_holdings
from backend.market_state import get_market_state, get_regime_message, get_state_emoji
from backend.inference import get_neumf_recommendations
from backend.optimization import optimize_portfolio
from backend.coin_metadata import enrich_recommendations, get_coin_symbol

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="PortfolioPulse API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request / Response Models ──────────────────────────────────────

class QuizRequest(BaseModel):
    answers: dict[str, str]  # {question_key: answer_key}


class RecommendRequest(BaseModel):
    user_idx: int
    risk_score: int
    market_state: str


class Holding(BaseModel):
    symbol: str
    amount: float


class ImportRequest(BaseModel):
    holdings: list[Holding]


# ─── Endpoints ──────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/market")
def market():
    """Returns current market state + metrics."""
    data = get_market_state()
    state = data['market_state']
    return {
        **data,
        'regime_message': get_regime_message(state),
        'emoji': get_state_emoji(state),
    }


@app.post("/api/quiz")
def quiz(req: QuizRequest):
    """Takes quiz answers → returns risk profile + proxy user."""
    risk_score = calculate_risk_score(req.answers)
    risk_label = get_risk_label(risk_score)
    match = find_nearest_user(risk_score)

    return {
        'risk_score': risk_score,
        'risk_label': risk_label,
        'proxy_user': match,
    }


@app.post("/api/recommend")
def recommend(req: RecommendRequest):
    """Full pipeline: NeuMF inference → optimization → enrichment."""
    # Step 1: Get NeuMF recommendations
    raw_recs = get_neumf_recommendations(req.user_idx)

    # Step 2: Build coin symbol map for stablecoin detection
    coin_symbols = {}
    for idx, _ in raw_recs:
        coin_symbols[idx] = get_coin_symbol(idx)

    # Step 3: Optimize portfolio
    optimized = optimize_portfolio(
        raw_recommendations=raw_recs,
        market_state=req.market_state,
        risk_score=req.risk_score,
        coin_symbols=coin_symbols,
    )

    # Step 4: Enrich with metadata, prices, explanations
    enriched = enrich_recommendations(
        allocations=optimized['allocations'],
        market_state=req.market_state,
    )

    return {
        'recommendations': enriched,
        'regime_explanation': optimized['regime_explanation'],
        'market_state': req.market_state,
        'risk_score': req.risk_score,
    }


@app.post("/api/import")
def import_portfolio(req: ImportRequest):
    """Import holdings → derive risk → full recommendation pipeline."""
    holdings_dicts = [{"symbol": h.symbol, "amount": h.amount} for h in req.holdings]

    # Analyze holdings to get risk profile + proxy user
    result = analyze_holdings(holdings_dicts)
    risk_score = result.get('risk_score', 3)
    risk_label = get_risk_label(risk_score)
    user_idx = result['user_idx']

    # Run full recommendation pipeline
    market_data = get_market_state()
    state = market_data['market_state']

    raw_recs = get_neumf_recommendations(user_idx)
    coin_symbols = {idx: get_coin_symbol(idx) for idx, _ in raw_recs}
    optimized = optimize_portfolio(raw_recs, state, risk_score, coin_symbols)
    enriched = enrich_recommendations(optimized['allocations'], state)

    return {
        'risk_score': risk_score,
        'risk_label': risk_label,
        'proxy_user': result,
        'market': {
            **market_data,
            'regime_message': get_regime_message(state),
            'emoji': get_state_emoji(state),
        },
        'recommendations': enriched,
        'regime_explanation': optimized['regime_explanation'],
    }

