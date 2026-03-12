# PortfolioPulse — README Reference Document

> Compile information from this document when writing your GitHub README. Pick and choose sections as needed.

---

## 1. Project Overview (One-Liner / Tagline)

- **One-liner:** AI-powered crypto portfolio advisor that delivers personalized token recommendations using neural collaborative filtering and real-time market regime analysis.
- **Tagline options:**
  - "Personalized crypto portfolio recommendations backed by ML and live market data"
  - "AI-driven token allocations tailored to your risk profile and current market conditions"

---

## 2. What It Does / Use Cases

- **Primary:** Users get personalized crypto portfolio recommendations based on their risk profile and current market regime.
- **Two entry flows:**
  1. **Quiz flow** — Answer 6 risk-profile questions → get a proxy user from the training set → NeuMF recommendations → regime-adjusted allocations.
  2. **Import flow** — Connect wallet (Mobula), upload CSV, or manually enter holdings → risk derived from portfolio composition → same recommendation pipeline.
- **Output:** Ranked token allocations with weights, confidence scores, explanations, donut chart, CSV export.
- **Demo mode:** Visit `/results?demo=true` to see sample recommendations without quiz or import.

---

## 3. Tech Stack

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | 16.1.6 | React framework, App Router |
| React | 19.2.3 | UI |
| TypeScript | 5.x | Type safety |
| Plotly.js / react-plotly.js | 2.35.2 / 2.6.0 | Donut chart visualization |
| Wagmi | 3.5.0 | Ethereum wallet hooks |
| Reown AppKit | 1.8.19 | Web3Modal-style wallet connection |
| Viem | 2.47.0 | Ethereum utilities |
| TanStack React Query | 5.90.21 | Data fetching / caching |
| PapaParse | 5.5.3 | Client-side CSV parsing |

- **Build:** Static export (`output: "export"`) — deploys as static HTML/JS.
- **Hosting:** AWS Amplify (frontend in `frontend/`, app root configured in `amplify.yml`).

### Backend
| Technology | Purpose |
|------------|---------|
| FastAPI | REST API (local dev) |
| Uvicorn | ASGI server |
| TensorFlow | NeuMF model inference (local fallback) |
| Pandas | Data loading, qualified wallets |
| NumPy | Numerical ops |
| scikit-learn | Utilities |
| PyPortfolioOpt | Mean-variance optimization |
| SciPy | Optimization routines |
| Boto3 | AWS (DynamoDB, SageMaker, S3) |
| Requests | CoinGecko API |
| python-dotenv | Env config |
| cachetools | TTL caching |

### AWS (Production)
| Service | Role |
|---------|------|
| AWS Amplify | Frontend hosting, CI/CD from GitHub |
| API Gateway | REST API, CORS, HTTPS |
| Lambda | Backend orchestrator (replaces FastAPI) |
| SageMaker Serverless | NeuMF inference endpoint |
| DynamoDB | Market state (Fear & Greed, RSI, volatility) |
| S3 | Model artifacts, data files |
| ECR | Lambda container image |
| CloudWatch | Logs, metrics, alarms |

### External APIs
| API | Purpose |
|-----|---------|
| CoinGecko | Token metadata, prices, 24h change |
| Mobula | Multi-chain wallet portfolio (80+ chains) |
| WalletConnect / Reown | Wallet connection |

---

## 4. Skills Demonstrated

- **Machine Learning:** NeuMF (Neural Matrix Factorization) for collaborative filtering; trained on 200k+ wallet interactions; inference via SageMaker or local TF.
- **Backend / API:** FastAPI, REST design, Lambda, API Gateway, CORS.
- **Frontend:** Next.js App Router, React 19, TypeScript, responsive UI, Web3 (WalletConnect, Mobula).
- **DevOps / Cloud:** AWS serverless (Lambda, SageMaker, DynamoDB, S3, Amplify), Docker, ECR, CI/CD.
- **Data Engineering:** CSV parsing, multi-source portfolio merge, DynamoDB, caching.
- **Finance / Quant:** Mean-variance optimization (PyPortfolioOpt), regime-based rules, risk constraints, stablecoin floors.

---

## 5. Architecture (High-Level)

```
User → Next.js (Amplify) → API Gateway → Lambda
                                    ├→ SageMaker (NeuMF)
                                    ├→ DynamoDB (market state)
                                    └→ S3 (model, data)
```

- **Local dev:** Next.js (`npm run dev`) + FastAPI (`uvicorn backend.api:app --port 8000`).
- **Production:** Amplify serves static frontend; API Gateway routes to Lambda; Lambda calls SageMaker, DynamoDB, S3.

---

## 6. Data Flow

1. **Quiz:** Answers → `calculate_risk_score` → `find_nearest_user` (proxy from `qualified_wallets.csv`) → `user_idx`.
2. **Import:** Holdings → `analyze_holdings` (risk from token count) → `find_nearest_user` → `user_idx`.
3. **Recommendations:** `user_idx` + `risk_score` + `market_state` → NeuMF inference → optimization (regime rules, risk caps) → enrichment (metadata, prices) → response.
4. **Market state:** DynamoDB `MarketState` table (or mock fallback) → Fear & Greed, RSI, volatility, regime message.

---

## 7. Key Files / Project Structure

```
PortfolioPulse/
├── frontend/           # Next.js app
│   ├── app/
│   │   ├── page.tsx    # Home
│   │   ├── quiz/       # Risk quiz
│   │   ├── import/     # Portfolio import
│   │   └── results/    # Recommendations + chart
│   ├── components/     # Navbar, ConnectWallet, etc.
│   └── lib/            # API client, DataIngestion (CSV, Mobula, merge)
├── backend/
│   ├── api.py          # FastAPI routes (dev)
│   ├── lambda_handler.py  # Lambda entry (prod)
│   ├── inference.py   # NeuMF: SageMaker → local TF → demo scores
│   ├── optimization.py # Regime rules, mean-variance, stablecoin floors
│   ├── profile_builder.py # Quiz scoring, find_nearest_user, analyze_holdings
│   ├── market_state.py # DynamoDB / mock market state
│   └── coin_metadata.py # Token metadata, CoinGecko prices
├── sm_endpoint/        # SageMaker deployment
│   ├── deploy.py
│   ├── inference.py
│   └── test_endpoint.py
├── data/               # CryptoInteractions.csv, coin_manifest.json, qualified_wallets.csv
├── models/             # neumf_model.keras (local inference)
├── amplify.yml         # Amplify build config
├── .env.template       # Env var template
└── Context/
    ├── AWS-Deployment-Architecture.md
    └── README-Reference.md (this file)
```

---

## 8. Development Process

### Prerequisites
- Node 20, Python 3.12+
- AWS CLI (for prod), Docker (for Lambda image)

### Local Setup

**Backend:**
```bash
cd PortfolioPulse
python -m pip install -r requirements.txt
python -m uvicorn backend.api:app --reload --host 127.0.0.1 --port 8000
```

**Frontend:**
```bash
cd frontend
cp ../.env.template .env.local   # Edit with your keys
npm install
npm run dev
```

**Env vars (frontend/.env.local):**
- `NEXT_PUBLIC_API_URL` — `http://localhost:8000` (no trailing slash)
- `NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID` — from cloud.reown.com
- `NEXT_PUBLIC_MOBULA_KEY` — from Mobula dashboard

### Data Files (Optional for full pipeline)
- `data/CryptoInteractions.csv` — training interactions
- `data/qualified_wallets.csv` — proxy users for cold-start
- `data/coin_manifest.json` — item_idx → symbol/name/coingecko_id
- `models/neumf_model.keras` — trained model (local inference fallback)

Without these, backend uses synthetic/demo fallbacks.

---

## 9. Deployment (Production)

- **Frontend:** Push to GitHub → Amplify auto-builds from `amplify.yml` (app root: `frontend`, output: `out`).
- **Backend:** Lambda (container from ECR) + API Gateway. See `Context/AWS-Deployment-Architecture.md` for full checklist.
- **ML:** SageMaker Serverless Inference for NeuMF (~$0–2/month, cold start 2–4 min after idle).

---

## 10. API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | Health check |
| GET | `/api/market` | Market state (Fear & Greed, RSI, regime) |
| POST | `/api/quiz` | Quiz answers → risk profile + proxy user |
| POST | `/api/recommend` | user_idx, risk_score, market_state → recommendations |
| POST | `/api/import` | Holdings → risk + recommendations |

---

## 11. ML Pipeline Summary

- **NeuMF:** Neural collaborative filtering; scores all tokens for a user; returns top-N by affinity.
- **Inference priority:** SageMaker endpoint → local TensorFlow model → deterministic demo scores (seeded RNG).
- **Optimization:** Regime rules (bull/bear/neutral/extreme_fear) set stablecoin floors and max single-asset caps; risk score adds personal constraints; PyPortfolioOpt mean-variance when price history available.
- **Enrichment:** CoinGecko metadata, prices, 24h change; generated explanations per token.

---

## 12. Disclaimer (Copy-Paste)

> This system identifies what historically profitable traders with your risk profile held during similar market conditions — then adjusts for current market regime. Do not take recommendations as strict financial advice.

---

## 13. License / Repo

- GitHub: `https://github.com/HemuTheReddy/PortfolioPulse`
- Add your chosen license (MIT, Apache 2.0, etc.) if desired.

---

## 14. Screenshots / Demo

- Suggest: hero, quiz, import (wallet/CSV/manual), results (allocations + chart), export CSV.
- Demo link: `/results?demo=true` (works with backend running).
