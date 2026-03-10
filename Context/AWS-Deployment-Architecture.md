# PortfolioPulse — Revised AWS Deployment Architecture

> Serverless architecture using SageMaker, Lambda, API Gateway, and DynamoDB. No EC2 required.

---

## Architecture Diagram

```
                        ┌──────────────┐
                        │   Route 53   │  (optional custom domain)
                        └──────┬───────┘
                               │
              ┌────────────────┴────────────────┐
              │                                  │
     ┌────────▼─────────┐            ┌───────────▼───────────┐
     │   AWS Amplify     │            │    API Gateway         │
     │   (Next.js)       │───────────▶│    (REST API)          │
     │   Frontend        │            └───────────┬───────────┘
     └──────────────────┘                         │
                                       ┌──────────▼──────────┐
                                       │   Lambda Function    │
                                       │   (Orchestrator)     │
                                       └──┬─────┬────────┬───┘
                                          │     │        │
                              ┌───────────▼┐  ┌─▼──────┐ │
                              │ SageMaker  │  │DynamoDB │ │
                              │ Endpoint   │  │(Market  │ │
                              │ (NeuMF)    │  │ State)  │ │
                              └────────────┘  └────────┘ │
                                                   ┌─────▼────┐
                                                   │    S3     │
                                                   │ (model,   │
                                                   │  data)    │
                                                   └──────────┘
```

---

## Why This Architecture?

| Benefit | Description |
|---------|-------------|
| **No server management** | No EC2 to patch, monitor, or keep running |
| **Scales to zero** | Pay nothing when nobody is using it |
| **Resume-impressive** | Demonstrates deep AWS knowledge (SageMaker, Lambda, API Gateway) |
| **HTTPS included** | API Gateway provides HTTPS out of the box — no NGINX/Certbot |
| **Cost-effective** | ~$0–2/month for a portfolio project |

---

## Full Deployment Checklist

### Phase 0: GitHub & Project Prep

| # | Task | Details |
|---|------|---------|
| 0.1 | Create `.gitignore` | Exclude `.venv/`, `node_modules/`, `.next/`, `.env`, `.env.local`, `models/`, `__pycache__/` |
| 0.2 | Init git repo | `git init && git add . && git commit -m "Initial commit"` |
| 0.3 | Create GitHub repo & push | `gh repo create PortfolioPulse --public --source=. --push` |
| 0.4 | Set up `.env.template` | Ensure it documents ALL required vars |

---

### Phase 1: AWS Foundation (S3 + DynamoDB)

| # | Task | Details |
|---|------|---------|
| 1.1 | AWS account + CLI setup | `aws configure` with your access key, secret, region |
| 1.2 | Create S3 bucket | `aws s3 mb s3://portfoliopulse-artifacts` — for model artifacts, data files |
| 1.3 | Upload NeuMF model to S3 | `aws s3 cp models/neumf_model.keras s3://portfoliopulse-artifacts/models/` |
| 1.4 | Upload data files to S3 | Upload `coin_manifest.json`, `CryptoInteractions.csv`, `qualified_wallets.csv` |
| 1.5 | Verify DynamoDB table | Ensure `MarketState` table exists (or create with on-demand billing) |

---

### Phase 2: SageMaker Endpoint (The ML Brain)

Deploy `neumf_model.keras` as a live serverless inference endpoint.

All scripts live in `sm_endpoint/`:

| File | Purpose |
|------|---------|
| `sm_endpoint/inference.py` | Custom inference handlers — runs ON the SageMaker container |
| `sm_endpoint/deploy.py` | Run locally — packages model, uploads to S3, deploys endpoint |
| `sm_endpoint/test_endpoint.py` | Run locally — verifies the endpoint works |

#### How the model gets packaged

SageMaker expects a `model.tar.gz` with this structure:

```
model.tar.gz/
  neumf_model.keras        ← the trained Keras model
  code/
    inference.py            ← custom handlers (model_fn, input_fn, predict_fn, output_fn)
```

The `deploy.py` script builds this automatically from your local `models/neumf_model.keras`.

#### Step-by-step

| # | Task | Details |
|---|------|---------|
| 2.0 | **Create SageMaker IAM Role** | See instructions below — required before anything else |
| 2.1 | Install SageMaker SDK locally | `python -m pip install \"sagemaker<3\"` (in your .venv) |
| 2.2 | Ensure model exists locally | Place `neumf_model.keras` in `models/`, or download from S3: `aws s3 cp s3://portfoliopulse-artifacts/models/neumf_model.keras models/` |
| 2.3 | Set environment variables | `SAGEMAKER_ROLE=arn:aws:iam::YOUR_ACCOUNT:role/PortfolioPulseSageMakerRole` |
| 2.4 | Run the deploy script | `python -m sm_endpoint.deploy` — packages, uploads, deploys (~5 min) |
| 2.5 | Test the endpoint | `python -m sm_endpoint.test_endpoint --user-idx 100 --top-n 10` |
| 2.6 | Add endpoint name to `.env` | `SAGEMAKER_ENDPOINT=portfoliopulse-neumf` |

#### Step 2.0: Create the SageMaker IAM Role (manual — AWS Console)

1. Go to **IAM Console** → Roles → Create role
2. Trusted entity: **AWS Service** → Use case: **SageMaker**
3. Name it: `PortfolioPulseSageMakerRole`
4. Attach these policies:
   - `AmazonSageMakerFullAccess` (managed policy)
   - Create an inline policy for S3 access:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::portfoliopulse-artifacts",
                "arn:aws:s3:::portfoliopulse-artifacts/*"
            ]
        }
    ]
}
```

5. After creating the role, copy its **ARN** — you need it for the deploy script.

#### Why Serverless Inference?

| | Real-time Endpoint | Serverless Inference |
|---|---|---|
| Cost | ~$36/month (ml.t2.medium 24/7) | ~$0–2/month (pay per invocation) |
| Cold start | None | ~2–4 min after idle (TF is heavy) |
| Scales to zero | No | Yes |
| Best for | Production traffic | Portfolio projects / demos |

Tradeoff: first request after idle takes 2–4 minutes while the TF container spins up. Subsequent requests are fast (~1–3 seconds). This is fine for a portfolio demo — just mention it in your README.

#### Request / Response format

**Request** (JSON):
```json
{
    "user_idx": 100,
    "top_n": 10
}
```

**Response** (JSON):
```json
{
    "recommendations": [
        {"item_idx": 0, "score": 0.892341},
        {"item_idx": 3, "score": 0.845123},
        ...
    ]
}
```

The Lambda function (Phase 3) will call this endpoint, then pass the results through the optimization and enrichment pipeline.

---

### Phase 3: Lambda Function (The Orchestrator)

Replaces the entire FastAPI backend. One Lambda handles all routes.

All code is implemented:

| File | Purpose |
|------|---------|
| `backend/lambda_handler.py` | Lambda entry point — routes API Gateway events to business logic |
| `backend/inference.py` | Updated — SageMaker endpoint → local TF model → demo scores (priority chain) |
| `requirements-lambda.txt` | Trimmed deps for Lambda container (no TF/FastAPI) |
| `Dockerfile` | Lambda container image definition |
| `.dockerignore` | Excludes frontend, models, .venv, etc. from image |

#### Deployment steps (AWS Console / CLI)

| # | Task | Details | Status |
|---|------|---------|--------|
| 3.1 | Create IAM role for Lambda | See IAM policy below | **AWS — manual** |
| 3.2 | Restructure backend code for Lambda | `backend/lambda_handler.py` created | **Done** |
| 3.3 | Build as container image | `docker build -t portfoliopulse-lambda .` | **Done (code)** |
| 3.4 | Create ECR repo + push image | See commands below | **AWS — manual** |
| 3.5 | Create Lambda function | From container image, 1024 MB memory, 60s timeout | **AWS — manual** |
| 3.6 | Set environment variables | `SAGEMAKER_ENDPOINT`, `DYNAMO_TABLE`, `AWS_REGION`, `AMPLIFY_DOMAIN` | **AWS — manual** |
| 3.7 | Test Lambda | Invoke via AWS console with sample payloads below | **AWS — manual** |

#### Step 3.1: Create the Lambda IAM Role (manual — AWS Console)

1. Go to **IAM Console** → Roles → Create role
2. Trusted entity: **AWS Service** → Use case: **Lambda**
3. Name it: `PortfolioPulseLambdaRole`
4. Attach managed policies:
   - `AWSLambdaBasicExecutionRole` (CloudWatch Logs)
5. Create an inline policy `PortfolioPulseLambdaAccess`:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "DynamoDBAccess",
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:Query",
                "dynamodb:Scan"
            ],
            "Resource": "arn:aws:dynamodb:*:*:table/MarketState"
        },
        {
            "Sid": "SageMakerInvoke",
            "Effect": "Allow",
            "Action": "sagemaker:InvokeEndpoint",
            "Resource": "arn:aws:sagemaker:*:*:endpoint/portfoliopulse-neumf"
        },
        {
            "Sid": "S3ReadData",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::portfoliopulse-artifacts",
                "arn:aws:s3:::portfoliopulse-artifacts/*"
            ]
        }
    ]
}
```

#### Step 3.4: Build & push container image to ECR

```bash
# 1. Create ECR repo (once)
aws ecr create-repository --repository-name portfoliopulse-lambda --region us-east-1

# 2. Authenticate Docker to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# 3. Build image
docker build -t portfoliopulse-lambda .

# 4. Tag for ECR
docker tag portfoliopulse-lambda:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/portfoliopulse-lambda:latest

# 5. Push
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/portfoliopulse-lambda:latest
```

#### Step 3.5: Create Lambda function (AWS Console)

1. Go to **Lambda Console** → Create function → **Container image**
2. Function name: `PortfolioPulse-API`
3. Container image URI: `YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/portfoliopulse-lambda:latest`
4. Execution role: `PortfolioPulseLambdaRole`
5. After creation, edit General configuration:
   - Memory: **1024 MB**
   - Timeout: **60 seconds**
   - Ephemeral storage: **512 MB** (default is fine)

#### Step 3.6: Set Lambda environment variables

| Key | Value |
|-----|-------|
| `SAGEMAKER_ENDPOINT` | `portfoliopulse-neumf` |
| `DYNAMO_TABLE` | `MarketState` |
| `AWS_REGION` | `us-east-1` |
| `AMPLIFY_DOMAIN` | *(set after Phase 5 — your Amplify URL)* |

#### Step 3.7: Test payloads

**Health check:**
```json
{
    "httpMethod": "GET",
    "path": "/api/health",
    "headers": {},
    "body": null
}
```

**Quiz:**
```json
{
    "httpMethod": "POST",
    "path": "/api/quiz",
    "headers": {"Content-Type": "application/json"},
    "body": "{\"answers\":{\"horizon\":\"1-6m\",\"loss\":\"hold\",\"experience\":\"1-3y\",\"volatility\":\"neutral\",\"capital\":\"5-15\",\"goal\":\"aggressive\"}}"
}
```

**Recommend:**
```json
{
    "httpMethod": "POST",
    "path": "/api/recommend",
    "headers": {"Content-Type": "application/json"},
    "body": "{\"user_idx\":100,\"risk_score\":3,\"market_state\":\"neutral\"}"
}
```

#### How inference works in Lambda

`backend/inference.py` uses a priority chain:
1. **SageMaker endpoint** — if `SAGEMAKER_ENDPOINT` env var is set, calls endpoint via `boto3 sagemaker-runtime`
2. **Local TF model** — if `models/neumf_model.keras` exists (dev only, not in Lambda container)
3. **Demo scores** — deterministic fallback using seeded RNG

This means the Lambda container does **not** need TensorFlow (~500 MB saved), since all ML inference runs on the SageMaker serverless endpoint.

**Why a container image?** `pyportfolioopt` depends on `scipy` (~70 MB). Lambda zip limit is 250 MB unzipped. Container images support up to **10 GB**.

---

### Phase 4: API Gateway (The Front Door)

No code changes needed — `lambda_handler.py` already handles proxy integration routing, CORS preflight, and stage prefix stripping. This phase is entirely AWS Console work.

**Strategy:** Use a single greedy path `{proxy+}` with Lambda Proxy Integration. All routing happens inside the Lambda handler, so you only configure one integration instead of five separate resources.

| # | Task | Details | Status |
|---|------|---------|--------|
| 4.1 | Create REST API | Name: `PortfolioPulse-API` | **AWS — manual** |
| 4.2 | Create `{proxy+}` resource | Greedy catch-all path under `/` | **AWS — manual** |
| 4.3 | Create `ANY` method on `{proxy+}` | Lambda Proxy Integration → `PortfolioPulse-API` | **AWS — manual** |
| 4.4 | Add root `ANY` method | Same integration on `/` for `/api/health` etc. | **AWS — manual** |
| 4.5 | Enable CORS | Enable on `{proxy+}` resource | **AWS — manual** |
| 4.6 | Deploy to `prod` stage | Creates the live URL | **AWS — manual** |
| 4.7 | Test the endpoints | Verify all 5 routes via the prod URL | **AWS — manual** |

#### Step 4.1: Create the REST API

1. Go to **API Gateway Console** (make sure region is **us-east-2**)
2. Click **Create API**
3. Choose **REST API** (not HTTP API, not WebSocket) → click **Build**
4. Settings:
   - API name: `PortfolioPulse-API`
   - Description: `PortfolioPulse serverless backend`
   - Endpoint Type: **Regional**
5. Click **Create API**

#### Step 4.2: Create the `{proxy+}` catch-all resource

1. In the left panel, click **Resources**
2. Select the root `/` resource
3. Click **Create Resource**
4. Check **Proxy resource** (this auto-fills `{proxy+}`)
5. Check **Enable API Gateway CORS**
6. Click **Create Resource**

#### Step 4.3: Create the `ANY` method on `{proxy+}`

After creating the proxy resource, API Gateway will prompt you to set up the integration:

1. Integration type: **Lambda Function**
2. Check **Use Lambda Proxy integration**
3. Lambda Region: `us-east-2`
4. Lambda Function: `PortfolioPulse-API`
5. Click **Save**
6. When prompted "Add Permission to Lambda Function?" click **OK**

#### Step 4.4: Add root `ANY` method (for paths like `/api/health` directly)

1. Select the root `/` resource
2. Click **Create Method**
3. Method type: **ANY**
4. Integration type: **Lambda Function**
5. Check **Use Lambda Proxy integration**
6. Lambda Region: `us-east-2`
7. Lambda Function: `PortfolioPulse-API`
8. Click **Save** → **OK** when prompted about permissions

#### Step 4.5: Verify CORS

CORS is handled in two places:
- **Preflight (OPTIONS):** The `{proxy+}` proxy resource auto-created an OPTIONS method when you checked "Enable API Gateway CORS" in step 4.2
- **Actual responses:** `lambda_handler.py` already includes `Access-Control-Allow-Origin` headers on every response

If you skipped the CORS checkbox in Step 4.2:
1. Select the `{proxy+}` resource
2. Click **Enable CORS**
3. Access-Control-Allow-Origin: `*` (we restrict this in Lambda code)
4. Access-Control-Allow-Methods: `GET, POST, OPTIONS`
5. Access-Control-Allow-Headers: `Content-Type, Authorization`
6. Click **Enable CORS and replace existing CORS headers**

#### Step 4.6: Deploy to `prod` stage

1. Click **Deploy API** (button at top)
2. Deployment stage: **New Stage**
3. Stage name: `prod`
4. Click **Deploy**

Your API URL will be:
```
https://{api-id}.execute-api.us-east-2.amazonaws.com/prod
```

Copy this URL — you'll need it for Phase 5 (frontend).

#### Step 4.7: Test the endpoints

Test directly in your browser or with `curl`:

**Health check (browser):**
```
https://{api-id}.execute-api.us-east-2.amazonaws.com/prod/api/health
```
Expected: `{"status": "ok"}`

**Market state (browser):**
```
https://{api-id}.execute-api.us-east-2.amazonaws.com/prod/api/market
```
Expected: JSON with `market_state`, `market_metrics`, `regime_message`, `emoji`

**Quiz (PowerShell):**
```powershell
Invoke-RestMethod -Uri "https://{api-id}.execute-api.us-east-2.amazonaws.com/prod/api/quiz" -Method POST -ContentType "application/json" -Body '{"answers":{"horizon":"1-6m","loss":"hold","experience":"1-3y","volatility":"neutral","capital":"5-15","goal":"aggressive"}}'
```

**Recommend (PowerShell):**
```powershell
Invoke-RestMethod -Uri "https://jsxq8qzerb.execute-api.us-east-2.amazonaws.com/prod/api/recommend" -Method POST -ContentType "application/json" -Body '{"user_idx":100,"risk_score":3,"market_state":"neutral"}'
```

#### How path routing works with the stage prefix

API Gateway prepends the stage name to the URL path: `/prod/api/health`. The Lambda receives `path: "/prod/api/health"`. The handler automatically strips the stage prefix:

```
/prod/api/health  →  /api/health  →  matched to GET /api/health route
```

This is handled by this logic in `lambda_handler.py`:
```python
if path.count("/") > 2 and not path.startswith("/api"):
    path = "/" + "/".join(path.split("/")[2:])
```

---

### Phase 5: Frontend Deployment (AWS Amplify)

Code-side changes are done:

| File | Change | Purpose |
|------|--------|---------|
| `amplify.yml` | Added `nvm use 18`, `.next/cache` caching, env echo | Ensures correct Node version and faster rebuilds |
| `frontend/next.config.ts` | Added `output: 'standalone'`, CoinGecko image domain | Required for Amplify SSR hosting |

#### Prerequisites

Before starting, you need your code pushed to GitHub. If you haven't already:

```bash
git add .
git commit -m "Phase 5: Amplify deployment config"
git push origin main
```

#### Deployment steps

| # | Task | Details | Status |
|---|------|---------|--------|
| 5.1 | Connect Amplify to GitHub | Link your repo | **AWS — manual** |
| 5.2 | Configure build settings | Amplify auto-detects `amplify.yml` | **AWS — manual** |
| 5.3 | Set environment variables | 4 env vars needed | **AWS — manual** |
| 5.4 | Deploy | Triggered automatically | **AWS — manual** |
| 5.5 | Copy Amplify domain | Update Lambda `AMPLIFY_DOMAIN` env var | **AWS — manual** |
| 5.6 | Redeploy API Gateway | CORS needs the Amplify domain | **AWS — manual** |
| 5.7 | Verify | Test all flows end-to-end | **AWS — manual** |

#### Step 5.1: Connect Amplify to GitHub

1. Go to **AWS Amplify Console** (make sure region is **us-east-2**)
2. Click **Create new app**
3. Source: **GitHub** → click **Connect**
4. Authorize AWS Amplify to access your GitHub account
5. Select your repository: `PortfolioPulse`
6. Select branch: `main`
7. Click **Next**

#### Step 5.2: Configure build settings

Amplify will auto-detect `amplify.yml` from your repo root. Verify these settings:

1. **App name**: `PortfolioPulse` (or whatever you prefer)
2. **Framework detected**: Next.js — SSR
3. **Build settings**: Should show "Using amplify.yml from repository"
   - If it doesn't detect it, manually set:
     - App root: `frontend`
     - Build command: `npm run build`
     - Output directory: `.next`
4. Click **Next**

#### Step 5.3: Set environment variables

Before clicking **Save and deploy**, expand **Advanced settings** → **Environment variables** and add:

| Key | Value | Where to find it |
|-----|-------|-------------------|
| `NEXT_PUBLIC_API_URL` | `https://{api-id}.execute-api.us-east-2.amazonaws.com/prod` | Your API Gateway prod URL from Phase 4 |
| `NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID` | Your WalletConnect project ID | [cloud.reown.com](https://cloud.reown.com) |
| `NEXT_PUBLIC_MOBULA_KEY` | Your Mobula API key | Your Mobula dashboard |
| `NEXT_PUBLIC_COINBASE_CLIENT_ID` | Your Coinbase OAuth client ID | Coinbase developer portal |

**Important:** Do NOT include a trailing slash on `NEXT_PUBLIC_API_URL`. The frontend appends paths like `/api/health` directly.

- Correct: `https://abc123.execute-api.us-east-2.amazonaws.com/prod`
- Wrong: `https://abc123.execute-api.us-east-2.amazonaws.com/prod/`

#### Step 5.4: Deploy

1. Click **Save and deploy**
2. Amplify will:
   - Clone your repo
   - Run `nvm use 18` → `npm ci` → `npm run build`
   - Deploy the built Next.js app
3. Wait for the build to complete (~3–5 minutes)
4. Check the build logs if anything fails — common issues:
   - **Node version**: If it fails on `nvm use 18`, try setting the Node version in Amplify Console → App settings → Build settings → Build image settings → Live package updates → Add `Node.js` version `18`
   - **Missing env vars**: The build log will show `NEXT_PUBLIC_API_URL=` (empty) if not set — go back and add it

#### Step 5.5: Copy the Amplify domain + update Lambda

After successful deployment:

1. Go to your app in Amplify Console → **Domain management**
2. Copy the domain, e.g. `main.d1abc2def3.amplifyapp.com`
3. Go to **Lambda Console** → `PortfolioPulse-API` → **Configuration** → **Environment variables**
4. Add/update: `AMPLIFY_DOMAIN` = `main.d1abc2def3.amplifyapp.com`

This allows the Lambda CORS handler to accept requests from your Amplify domain.

#### Step 5.6: Verify CORS works end-to-end

After updating the Lambda env var, test that the frontend can talk to the API:

1. Open your Amplify URL in a browser: `https://main.d1abc2def3.amplifyapp.com`
2. Open browser DevTools → **Network** tab
3. Navigate to the Quiz page and submit — watch for:
   - `POST /api/quiz` → should return `200`
   - If you see CORS errors, check:
     - The `AMPLIFY_DOMAIN` env var in Lambda matches your actual domain exactly
     - The API Gateway is deployed (re-deploy if you made changes)

#### Step 5.7: Test all flows

| Test | How | Expected |
|------|-----|----------|
| Landing page loads | Visit Amplify URL | Hero section with "Take the Quiz" and "Import My Portfolio" buttons |
| Quiz flow | Click "Take the Quiz" → answer all questions → submit | Results page with allocations, donut chart, regime banner |
| Import flow | Click "Import My Portfolio" → connect wallet or enter holdings | Results page with risk profile derived from holdings |
| Market state | Check the stats row on results page | Shows current market regime (bull/bear/neutral) with source |
| CSV export | Click "Export CSV" on results page | Downloads a `.csv` file with all recommendations |
| Demo mode | Visit `/results?demo=true` directly | Shows demo results using user 42 |

#### Subsequent deployments

After the initial setup, every push to `main` triggers an automatic rebuild:

```bash
git add .
git commit -m "Your change description"
git push origin main
```

Amplify detects the push, rebuilds, and deploys automatically (~3–5 min).

---

### Phase 6: Monitoring (CloudWatch)

| # | Task | Details |
|---|------|---------|
| 6.1 | Lambda logs | Automatic — every invocation logs to CloudWatch Logs |
| 6.2 | SageMaker endpoint metrics | Monitor `Invocations`, `ModelLatency`, `OverheadLatency` |
| 6.3 | API Gateway metrics | Monitor `Count`, `Latency`, `4XXError`, `5XXError` |
| 6.4 | (Optional) Create dashboard | Single CloudWatch dashboard combining all three |
| 6.5 | (Optional) Set alarms | Alert if error rate > 5% or latency > 10s |

---

### Phase 7: Final Wiring & Testing

| # | Task | Details |
|---|------|---------|
| 7.1 | Update frontend API URL | Point to API Gateway prod URL |
| 7.2 | End-to-end test | Quiz flow → results, Import flow → results |
| 7.3 | Cold start test | Hit SageMaker after idle — document expected latency |
| 7.4 | Update GitHub README | Architecture diagram, setup instructions, live demo link |

---

## Cost Estimate (Monthly)

| Service | Cost |
|---------|------|
| SageMaker Serverless Inference | ~$0–2 (pay per invocation, scales to zero) |
| Lambda | ~$0 (free tier: 1M requests/month) |
| API Gateway | ~$0 (free tier: 1M calls/month for 12 months) |
| DynamoDB (on-demand) | ~$0 (free tier) |
| S3 | ~$0 (free tier) |
| Amplify Hosting | ~$0 (free tier) |
| ECR (container storage) | ~$0 (500 MB free) |
| CloudWatch | ~$0 (basic free) |
| **Total** | **~$0–2/month** |

---

## EC2 vs Serverless

| Previously (EC2) | Now (Serverless) |
|-------------------|------------------|
| EC2 running Uvicorn + FastAPI | Lambda + API Gateway |
| TensorFlow inference on EC2 | SageMaker Serverless Endpoint |
| systemd to keep server alive | Lambda is managed by AWS |
| NGINX + Certbot for HTTPS | API Gateway provides HTTPS |
| SSH in to deploy updates | Push to ECR → update Lambda |

**EC2 is not needed** for this architecture. The only scenario where you'd want EC2 is persistent WebSocket connections or long-running background processes. This app is request/response, so serverless fits well.
