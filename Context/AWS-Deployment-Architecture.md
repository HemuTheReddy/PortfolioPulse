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

Deploy `neumf_model.keras` as a live inference endpoint.

| # | Task | Details |
|---|------|---------|
| 2.1 | Create SageMaker inference script | Define `model_fn`, `input_fn`, `predict_fn`, `output_fn` for Keras model |
| 2.2 | Package model for SageMaker | Create `model.tar.gz` containing model + inference script, upload to S3 |
| 2.3 | Create SageMaker Model | Point to S3 `model.tar.gz` + TensorFlow serving container |
| 2.4 | Deploy as **Serverless Inference Endpoint** | Use `ServerlessInferenceConfig` — scales to zero, pay per request |
| 2.5 | Test the endpoint | Invoke with sample payload via `boto3` or AWS console |

**Why Serverless Inference?** A real-time SageMaker endpoint (ml.t2.medium) runs 24/7 (~$36/month). **Serverless Inference** scales to zero and costs fractions of a cent per invocation. Tradeoff: cold start of ~1–2 minutes on first request after idle.

**Example deployment code:**

```python
import sagemaker
from sagemaker.tensorflow import TensorFlowModel

role = "arn:aws:iam::YOUR_ACCOUNT:role/SageMakerExecutionRole"

model = TensorFlowModel(
    model_data="s3://portfoliopulse-artifacts/models/model.tar.gz",
    role=role,
    framework_version="2.13",
)

predictor = model.deploy(
    serverless_inference_config=sagemaker.serverless.ServerlessInferenceConfig(
        memory_size_in_mb=4096,
        max_concurrency=1,
    )
)
```

---

### Phase 3: Lambda Function (The Orchestrator)

Replaces the entire FastAPI backend. One Lambda handles all routes.

| # | Task | Details |
|---|------|---------|
| 3.1 | Create IAM role for Lambda | Permissions: `dynamodb:*`, `sagemaker:InvokeEndpoint`, `s3:GetObject`, `logs:*` |
| 3.2 | Restructure backend code for Lambda | Refactor `api.py` handlers into Lambda-compatible functions |
| 3.3 | Build as container image | Dependencies (scipy, pyportfolioopt, numpy, pandas) too large for zip — use Docker |
| 3.4 | Create ECR repo + push image | `aws ecr create-repository --repository-name portfoliopulse-lambda` |
| 3.5 | Create Lambda function | From container image, 1024 MB memory, 60s timeout |
| 3.6 | Set environment variables | API keys, SageMaker endpoint name, DynamoDB table name, S3 bucket |
| 3.7 | Test Lambda | Invoke via AWS console with sample payloads |

**Lambda handler structure:**

```python
import json
import boto3

sagemaker_runtime = boto3.client("sagemaker-runtime")
dynamodb = boto3.resource("dynamodb")

def handler(event, context):
    path = event["path"]
    method = event["httpMethod"]
    body = json.loads(event.get("body") or "{}")

    if path == "/api/health":
        return response(200, {"status": "healthy"})

    elif path == "/api/market":
        return get_market_state()

    elif path == "/api/quiz" and method == "POST":
        return process_quiz(body)

    elif path == "/api/recommend" and method == "POST":
        # 1. Get market state from DynamoDB
        market = get_market_state_from_dynamo()
        # 2. Call SageMaker for asset picks
        picks = invoke_sagemaker(body["risk_score"], market)
        # 3. Run optimization for final weights
        weights = optimize_portfolio(picks, market)
        return response(200, weights)

    elif path == "/api/import" and method == "POST":
        return process_import(body)

    return response(404, {"error": "Not found"})
```

**Why a container image?** `pyportfolioopt` depends on `scipy` (~70 MB). Lambda zip limit is 250 MB unzipped. Container images support up to **10 GB**.

**Dockerfile for Lambda:**

```dockerfile
FROM public.ecr.aws/lambda/python:3.11

COPY requirements-lambda.txt .
RUN pip install -r requirements-lambda.txt

COPY backend/ backend/
COPY data/ data/

CMD ["backend.lambda_handler.handler"]
```

---

### Phase 4: API Gateway (The Front Door)

| # | Task | Details |
|---|------|---------|
| 4.1 | Create REST API in API Gateway | Name: `PortfolioPulse-API` |
| 4.2 | Create resources & methods | `POST /api/quiz`, `POST /api/recommend`, `POST /api/import`, `GET /api/market`, `GET /api/health` |
| 4.3 | Integrate each method with Lambda | Proxy integration → single Lambda handles routing |
| 4.4 | Enable CORS | Allow Amplify domain + localhost:3000 |
| 4.5 | Deploy to a stage | Create `prod` stage → URL like `https://xxx.execute-api.us-east-1.amazonaws.com/prod` |
| 4.6 | (Optional) Custom domain | Map `api.yourdomain.com` to API Gateway |

**Shortcut:** Use **Lambda Proxy Integration** with greedy path `{proxy+}`. Forwards all requests to one Lambda for internal routing.

---

### Phase 5: Frontend Deployment (AWS Amplify)

| # | Task | Details |
|---|------|---------|
| 5.1 | Connect Amplify to GitHub | AWS Console → Amplify → Host Web App → GitHub |
| 5.2 | Set app root to `frontend` | Build settings: `appRoot: frontend` |
| 5.3 | Set environment variables | `NEXT_PUBLIC_API_URL` = API Gateway URL |
| 5.4 | Set remaining env vars | `NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID`, `NEXT_PUBLIC_MOBULA_KEY` |
| 5.5 | Deploy | Amplify auto-builds on push to `main` |
| 5.6 | Verify | Hit Amplify URL, test all flows |

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
