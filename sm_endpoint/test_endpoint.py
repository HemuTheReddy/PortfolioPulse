"""
test_endpoint.py — Invoke the SageMaker endpoint to verify it works.

Usage:
    python -m sm_endpoint.test_endpoint
    python -m sm_endpoint.test_endpoint --user-idx 42 --top-n 10
"""
import os
import json
import argparse
import time
import boto3

ENDPOINT_NAME = os.getenv("SAGEMAKER_ENDPOINT", "portfoliopulse-neumf")
AWS_REGION = os.getenv("AWS_REGION", "us-east-2")


def invoke_endpoint(user_idx: int, top_n: int = 20):
    """Send a prediction request to the SageMaker endpoint."""
    client = boto3.client("sagemaker-runtime", region_name=AWS_REGION)

    payload = json.dumps({
        "user_idx": user_idx,
        "top_n": top_n,
    })

    print(f"Invoking endpoint '{ENDPOINT_NAME}' ...")
    print(f"  user_idx = {user_idx}")
    print(f"  top_n    = {top_n}")
    print()

    start = time.time()

    response = client.invoke_endpoint(
        EndpointName=ENDPOINT_NAME,
        ContentType="application/json",
        Accept="application/json",
        Body=payload,
    )

    elapsed = time.time() - start
    body = json.loads(response["Body"].read().decode("utf-8"))

    print(f"Response received in {elapsed:.2f}s")
    print(f"HTTP status: {response['ResponseMetadata']['HTTPStatusCode']}")
    print()

    recs = body.get("recommendations", [])
    print(f"Top {len(recs)} recommendations:")
    print(f"{'Rank':<6} {'Item':>6} {'Score':>10}")
    print("-" * 24)

    for i, rec in enumerate(recs, 1):
        item_idx = rec["item_idx"]
        score = rec["score"]
        print(f"{i:<6} {item_idx:>6} {score:>10.6f}")

    return body


def check_endpoint_status():
    """Check if the endpoint exists and its current status."""
    client = boto3.client("sagemaker", region_name=AWS_REGION)
    try:
        resp = client.describe_endpoint(EndpointName=ENDPOINT_NAME)
        status = resp["EndpointStatus"]
        print(f"Endpoint '{ENDPOINT_NAME}' status: {status}")
        if status != "InService":
            print("Endpoint is not ready yet. Wait for status = InService.")
            return False
        return True
    except client.exceptions.ClientError:
        print(f"Endpoint '{ENDPOINT_NAME}' not found.")
        print("Run 'python -m sm_endpoint.deploy' first.")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test the PortfolioPulse SageMaker endpoint")
    parser.add_argument("--user-idx", type=int, default=100, help="User index to test (default: 100)")
    parser.add_argument("--top-n", type=int, default=10, help="Number of results (default: 10)")
    parser.add_argument("--status-only", action="store_true", help="Only check endpoint status")
    args = parser.parse_args()

    if args.status_only:
        check_endpoint_status()
        return

    if not check_endpoint_status():
        return

    print()
    invoke_endpoint(args.user_idx, args.top_n)


if __name__ == "__main__":
    main()
