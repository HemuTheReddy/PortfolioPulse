# PortfolioPulse
### [Website](https://main.d2ekmsbtyf11hx.amplifyapp.com/)

> **AI-powered crypto portfolio advisor** — personalized token recommendations using Neural Matrix Factorization, trained on 200K+ interactions from verified profitable wallets, adjusted in real time for current market regime.

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.x-orange?logo=tensorflow)
![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)
![AWS](https://img.shields.io/badge/AWS-Lambda%20%7C%20SageMaker%20%7C%20DynamoDB-yellow?logo=amazon-aws)
![BigQuery](https://img.shields.io/badge/BigQuery-Ethereum%20Data-blue?logo=google-cloud)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

---

## Preview

![Unavailable](assets/cryptodemo.png)

---

## What It Does

PortfolioPulse answers a specific question: *given your risk tolerance and current market conditions, what were historically profitable traders actually holding?*

It extracts behavioral data from 5,000 verified profitable Ethereum wallets, trains a Neural Matrix Factorization model on their token interactions, and serves personalized allocation recommendations — with real-time regime adjustments (bull/bear/high volatility/extreme fear) pulling live from AWS DynamoDB.

The system doesn't predict prices. It surfaces what investors with a documented track record of profitable exits held during similar market conditions, then optimizes allocation weights for your personal risk profile.

---

## Key Features

- **Collaborative filtering on verified profitable wallets** — training data filtered to wallets with ≥35% win rate (20%+ profitable trade exits), not all wallets regardless of outcome
- **Neural Matrix Factorization (NeuMF)** — dual-branch GMF + MLP architecture captures both linear and non-linear user-item affinity
- **Real-time market regime integration** — Fear & Greed index, RSI, and volatility pulled from DynamoDB hourly; stablecoin floors and position caps adjust automatically per regime
- **Cold-start solution via nearest-neighbor proxy** — new users matched to the closest behavioral archetype from the training set; personalized from the first interaction
- **Multi-source portfolio import** — Mobula API (80+ chains), CSV upload, or manual entry; all paths feed the same recommendation pipeline
- **Mean-variance optimization** — PyPortfolioOpt Efficient Frontier maximizes Sharpe Ratio when price history is available
- **Serverless ML inference** — SageMaker Serverless Inference with Lambda fallback to local TensorFlow; demo mode as final fallback

---

## Tech Stack

### Frontend
| Technology | Version | Purpose |
|---|---|---|
| Next.js | 16.1.6 | React framework, App Router, static export |
| React | 19.2.3 | UI |
| TypeScript | 5.x | Type safety |
| Plotly.js / react-plotly.js | 2.35.2 / 2.6.0 | Interactive donut chart |
| Wagmi + Viem | 3.5.0 / 2.47.0 | Ethereum wallet hooks |
| Reown AppKit | 1.8.19 | Web3Modal wallet connection |
| TanStack React Query | 5.90.21 | Data fetching and caching |
| PapaParse | 5.5.3 | Client-side CSV parsing |

### Backend
| Technology | Purpose |
|---|---|
| FastAPI + Uvicorn | REST API (local dev) |
| TensorFlow / Keras | NeuMF model — training and local inference |
| PyPortfolioOpt | Mean-variance optimization, Efficient Frontier |
| Boto3 | AWS integration — DynamoDB, SageMaker, S3 |
| Web3.py | Direct ERC-20 on-chain metadata via public RPC |
| Pandas / NumPy | Data processing, feature engineering |

### AWS (Production)
| Service | Role |
|---|---|
| Amplify | Frontend hosting, CI/CD from GitHub |
| API Gateway | REST API, CORS, HTTPS |
| Lambda | Backend orchestrator (container via ECR) |
| SageMaker Serverless | NeuMF inference (~$0–2/month) |
| DynamoDB | Market state: Fear & Greed, RSI, volatility |
| S3 | Model artifacts, data files |
| CloudWatch | Logs, metrics, alarms |

### Data & ML
| Technology | Purpose |
|---|---|
| Google BigQuery | 136GB+ Ethereum transaction history — free public dataset |
| CoinGecko API | Token metadata, prices, 24h change |
| Mobula API | Multi-chain wallet portfolio data |

---

## Architecture

```
User → Next.js (Amplify)
           │
           ▼
     API Gateway (HTTPS)
           │
           ▼
        Lambda
       ┌────┼────────────┐
       ▼    ▼            ▼
  SageMaker  DynamoDB    S3
  (NeuMF)   (market     (model,
             state)      data)
```

**Request flow:**
1. User completes quiz or imports portfolio → risk score computed
2. Risk score maps to a proxy wallet (nearest neighbor from `qualified_wallets.csv`)
3. Proxy `user_idx` + `risk_score` + live `market_state` sent to Lambda
4. Lambda calls SageMaker for NeuMF inference scores across all tokens
5. Regime rules applied (stablecoin floors, position caps) → PyPortfolioOpt optimization
6. Token metadata and prices fetched from CoinGecko → response returned

**Local dev:** `Next.js (npm run dev)` + `FastAPI (uvicorn --port 8000)`

---

## Data Pipeline

### Source
The Ethereum blockchain via Google BigQuery's free public dataset — 136GB+ of token transfer history, processed in ~30 seconds at $0.68 using automatic parallelization across ~433 concurrent workers.

### Wallet Quality Filter
Rather than using any wallet's transaction history, the pipeline filters down to genuinely profitable traders via a 7-stage multi-CTE BigQuery query:

1. **TokenPriceProxy** — Eliminate scam tokens, illiquid contracts, and dead tokens before wallet analysis
2. **WalletBehavior / WalletReceives** — Aggregate send-side and receive-side interactions per wallet-token pair
3. **WalletTokenPnL** — Compute `pnl_ratio` (value sent / value received) and `hold_duration_days` per trade
4. **WalletScores** — Score wallets holistically: win rate, active days, token diversity; apply minimum thresholds
5. **WalletTiered** — NTILE window functions to assign diversity buckets (split into its own CTE — BigQuery does not allow nested window functions)
6. **QualifiedWallets** — Stratified selection: top performers from each diversity bucket to ensure behavioral variety

**Final wallet set:** 5,000 wallets, avg win rate 46%, avg hold duration 40 days, perfectly stratified across 4 behavioral buckets (1,250 each)

### Interaction Dataset
A second query joins the 5,000 qualified wallets against the full transfer history to generate training interactions.

**Implicit rating construction** (no explicit ratings exist in on-chain data):
- 50% weight: log-scaled interaction frequency
- 30% weight: log-scaled total value moved
- 20% weight: active days on the token

**Post-generation cleanup removed:**
- Single-interaction pairs (52.2% of initial rows) — accidental transfers, airdrops, dust attacks provide no collaborative filtering signal
- Outlier pairs with >1,000 interactions — likely liquidity pool contracts or bots
- Applied min-max rescaling to normalize ratings from a compressed range (avg: 0.116, stddev: 0.049) to the full [0, 1]

**Final dataset:** 32,213 interactions · 4,922 unique users · 2,758 unique tokens · 80/10/10 train/val/test split

---

## ML Methodology

### Model: Neural Matrix Factorization (NeuMF)

NeuMF runs two parallel branches over the same user and item embeddings (dim=32):

- **GMF branch** — element-wise product of user and item embeddings; captures linear affinity (if similar users consistently hold a token, the dot product reflects this directly)
- **MLP branch** — concatenates user and item embeddings and passes through `[64, 32, 16]` dense layers; captures non-linear conditional preferences GMF cannot represent
- **Fusion** — both branch outputs concatenated and passed through a sigmoid-activated dense layer → predicted affinity score in [0, 1]

**Negative sampling:** 1:1 ratio of unseen items per user. A 2:1 ratio was tested but produced unstable validation AUC given dataset sparsity.

### Hyperparameters
| Parameter | Value | Rationale |
|---|---|---|
| Embedding dimension | 32 | Balanced capacity for a sparse dataset |
| MLP architecture | [64, 32, 16] | Reduced from [128, 64, 32] after overfitting diagnosis |
| Dropout | 0.5 | Aggressive regularization for sparse data |
| L2 regularization | 1e-3 | Strengthened from 1e-4 after diagnosing overfitting |
| Learning rate | 0.0005 | Halved from 0.001 to slow convergence |
| Loss | Binary cross-entropy | Standard for implicit feedback |

### Portfolio Optimization Layer
Raw NeuMF scores aren't portfolio weights. A two-stage optimization is applied:

**Stage 1 — Market Regime Rules (from DynamoDB)**
| Regime | Stablecoin Floor | Max Single Position |
|---|---|---|
| extreme_fear | 30% | 20% |
| bear | 20% | 25% |
| high_volatility | 15% | 30% |
| neutral | 5% | 35% |
| bull | 0% | 40% |

**Stage 2 — Personal Risk Rules**
Quiz risk score (1–5) applies independent position limits. The more conservative of regime constraints and personal risk constraints is applied — neither overrides the other.

Affinity scores converted to weights via softmax normalization → clipped to constraint → renormalized. When price history is available, PyPortfolioOpt Efficient Frontier maximizes the Sharpe Ratio instead.

---

## Challenges & How I Solved Them

### 1. BigQuery Type System — Ethereum Values Stored as Strings
**Problem:** The `value` column in BigQuery's Ethereum dataset is `STRING`, not a number. ERC-20 token values are 256-bit integers that exceed `INT64`. Initial query failed immediately with `No matching signature for operator > for argument types: STRING, INT64`.

**Attempts:**
- `CAST AS NUMERIC` — failed, values exceeded 29-digit precision
- `CAST AS BIGNUMERIC` — failed, certain tokens had 40+ digit values (e.g., scam tokens with astronomically inflated supplies)
- `SAFE_CAST AS BIGNUMERIC` — **success.** Returns `NULL` instead of throwing on unparseable values; combined with `IS NOT NULL` filter silently drops bad records

**Insight:** The tokens that failed to cast were almost certainly fraudulent — scam tokens with manipulated supplies. Handling the type error directly improved data quality as a side effect.

---

### 2. Aggregation Overflow at Scale
**Problem:** Even after fixing the type cast, `SUM()` across a wallet's BIGNUMERIC transactions exceeded the BIGNUMERIC limit at the aggregation level.

**Fix:** Normalize values before summing by dividing by `1e18` (standard ERC-20 decimal conversion):
```sql
SUM(SAFE_DIVIDE(SAFE_CAST(value AS BIGNUMERIC), BIGNUMERIC '1000000000000000000'))
```
Since normalization applies equally to both sends and receives, the `pnl_ratio` (sends / receives) is mathematically unchanged — only the absolute magnitudes are affected.

---

### 3. Nested Window Functions (BigQuery Limitation)
**Problem:** The initial `QualifiedWallets` CTE tried to use `NTILE()` inside the `PARTITION BY` clause of `ROW_NUMBER()`. BigQuery rejected this: `Analytic function not allowed in PARTITION BY`.

**Fix:** Split into two sequential CTEs. `WalletTiered` pre-computes NTILE assignments as ordinary columns; `QualifiedWallets` reads those columns in `PARTITION BY` as plain integers. Lesson: in BigQuery, window functions cannot be composed — intermediate results must materialize as CTEs.

---

### 4. Overfitting — Train AUC 0.99, Val AUC 0.87
**Problem:** With only 6.54 average interactions per user, the MLP had enough parameters to memorize individual user patterns rather than learning generalizable behavioral representations. The train/val gap emerged around epoch 10 and widened continuously.

**Fixes applied simultaneously:**
- Dropout: 0.3 → **0.5**
- L2 regularization: 1e-4 → **1e-3**
- MLP architecture: [128, 64, 32] → **[64, 32, 16]**
- Learning rate: 0.001 → **0.0005**
- Negative sampling ratio: 2:1 → **1:1** (2:1 added excessive noise to a sparse dataset)
- Early stopping: switched from monitoring `val_auc` to `val_loss` — loss began rising several epochs before AUC plateaued, providing an earlier and more reliable stopping signal

---

### 5. API Blocking — TLS Fingerprinting
**Problem:** CoinGecko's REST API returned `ConnectionResetError: [WinError 10054]` — the server accepted the connection then immediately closed it at the TLS handshake level, before any request was sent. Identified as TLS fingerprinting detecting Python's SSL stack as automated traffic. Adding a browser `User-Agent` header did not resolve it.

**Fix:** Pivoted to Web3.py for token metadata — direct ERC-20 `name()` and `symbol()` RPC calls against free public Ethereum nodes. No API key, no rate limits, cannot be fingerprinted, reads directly from the canonical source of truth. This eliminated the third-party API dependency entirely for the metadata pipeline.

---

## Setup & Installation

### Prerequisites
- Node 20+, Python 3.12+
- AWS CLI (for production deployment)
- Docker (for Lambda container builds)

### Local Development

**Backend:**
```bash
git clone https://github.com/HemuTheReddy/PortfolioPulse
cd PortfolioPulse
pip install -r requirements.txt
uvicorn backend.api:app --reload --host 127.0.0.1 --port 8000
```

**Frontend:**
```bash
cd frontend
cp ../.env.template .env.local   # Fill in your keys
npm install
npm run dev
```

**Required environment variables (`frontend/.env.local`):**
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID=<from cloud.reown.com>
NEXT_PUBLIC_MOBULA_KEY=<from Mobula dashboard>
```

**Optional data files** (backend uses demo fallbacks without them):
```
data/CryptoInteractions.csv     # Training interactions
data/qualified_wallets.csv      # Proxy users for cold-start
data/coin_manifest.json         # item_idx → symbol/name/coingecko_id mapping
models/neumf_model.keras         # Trained model for local inference
```

### Production Deployment
- **Frontend:** Push to GitHub → Amplify auto-builds from `amplify.yml`
- **Backend:** Lambda container from ECR + API Gateway — see `Context/AWS-Deployment-Architecture.md`
- **ML:** SageMaker Serverless Inference for NeuMF (~$0–2/month; cold start 2–4 min after idle)

---

## API Reference

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/market` | Live market state — Fear & Greed, RSI, regime |
| POST | `/api/quiz` | Quiz answers → risk score + proxy user |
| POST | `/api/recommend` | `user_idx`, `risk_score`, `market_state` → recommendations |
| POST | `/api/import` | Holdings → risk derivation + recommendations |

---

## Project Structure

```
PortfolioPulse/
├── frontend/                    # Next.js app (static export)
│   ├── app/
│   │   ├── page.tsx             # Home
│   │   ├── quiz/                # Risk quiz flow
│   │   ├── import/              # Portfolio import (wallet/CSV/manual)
│   │   └── results/             # Recommendations + donut chart
│   ├── components/              # Navbar, ConnectWallet, etc.
│   └── lib/                     # API client, DataIngestion (CSV, Mobula, merge)
├── backend/
│   ├── api.py                   # FastAPI routes (local dev)
│   ├── lambda_handler.py        # Lambda entry point (production)
│   ├── inference.py             # NeuMF: SageMaker → local TF → demo fallback
│   ├── optimization.py          # Regime rules, mean-variance, stablecoin floors
│   ├── profile_builder.py       # Quiz scoring, nearest-neighbor matching
│   ├── market_state.py          # DynamoDB market state reader
│   └── coin_metadata.py         # Token metadata, CoinGecko prices
├── sm_endpoint/                 # SageMaker deployment scripts
├── data/                        # Interactions CSV, coin manifest, qualified wallets
├── models/                      # neumf_model.keras (local inference fallback)
├── amplify.yml                  # Amplify build config
└── Context/
    └── AWS-Deployment-Architecture.md
```

---

## What I Learned

**You can't separate data quality from model quality.** The most consequential decisions in this project weren't architectural — they were filtering choices. Training on all wallets vs. profitable wallets, keeping single-touch interactions vs. removing them, using raw ratings vs. rescaling them all changed the model's behavior more than any hyperparameter.

**Cloud-native debugging requires different intuitions.** Several failures — BIGNUMERIC overflow, nested window functions, RAND() evaluated twice — only occur at scale or in specific SQL engines. The fix for each was not debugging code but understanding what the infrastructure actually does.

**Pivoting dependencies early matters.** The TLS fingerprinting issue with CoinGecko could have been patched indefinitely with headers and delays. Treating it as signal to eliminate the dependency entirely made the metadata pipeline more reliable and architecturally cleaner.

---

## Future Improvements

- **Fill in test metrics** — complete the NeuMF test AUC, Hit Rate @10, and MAE/RMSE evaluation once final model training is complete
- **Context-aware embeddings** — incorporate market state as a third embedding branch fused at the final concatenation layer, so the model learns regime-conditional preferences rather than applying regime rules as a post-processing step
- **Temporal signal** — add recency weighting to interactions so recent holdings carry more signal than trades from two years ago
- **On-chain portfolio refresh** — real-time sync via Mobula webhooks rather than polling on page load
- **Multi-chain expansion** — extend training data beyond Ethereum to include Solana and Base chain wallets

---

## Disclaimer

> This system identifies what historically profitable traders with your risk profile held during similar market conditions — then adjusts allocations for current market regime. Do not treat recommendations as financial advice.

---

## License

[MIT](LICENSE) · GitHub: [HemuTheReddy/PortfolioPulse](https://github.com/HemuTheReddy/PortfolioPulse)
