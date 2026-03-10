"""
deploy.py - Package the NeuMF model and deploy to SageMaker Serverless Inference.

Run this locally ONCE to set up the endpoint:
    python -m sm_endpoint.deploy

Prerequisites:
    1. Virtual environment activated:  .venv/Scripts/Activate.ps1
    2. Dependencies installed:         pip install -r requirements.txt
    3. AWS CLI configured:             aws configure
    4. Model file at models/neumf_model.keras
    5. SAGEMAKER_ROLE env var set to your IAM role ARN
"""
import os
import sys
import tarfile
import shutil
import tempfile


def _preflight_check():
    """Verify the environment has all required packages and correct versions before doing any work."""
    errors = []

    # Detect if running outside the .venv
    exe = sys.executable.replace("\\", "/")
    if ".venv" not in exe:
        errors.append(
            f"Not running inside the virtual environment.\n"
            f"  Current Python: {sys.executable}\n"
            f"  Fix: open PowerShell in the PortfolioPulse folder and run:\n"
            f"       .venv\\Scripts\\Activate.ps1\n"
            f"       python -m sm_endpoint.deploy"
        )

    # Python version
    major, minor = sys.version_info[:2]
    if (major, minor) < (3, 9):
        errors.append(f"Python 3.9+ required, found {major}.{minor}")

    # Required packages
    required = {
        "boto3": "boto3",
        "sagemaker": "sagemaker",
        "tensorflow": "tensorflow",
        "botocore": "botocore",
    }
    missing = []
    for display, module in required.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(display)

    if missing:
        errors.append(
            f"Missing packages: {', '.join(missing)}\n"
            "  Fix: activate the virtual environment and run:\n"
            "       .venv\\Scripts\\Activate.ps1\n"
            "       pip install -r requirements.txt"
        )

    if errors:
        print("\n" + "=" * 60)
        print("  PREFLIGHT CHECK FAILED")
        print("=" * 60)
        for err in errors:
            print(f"\n  ERROR: {err}")
        print("\n" + "=" * 60)
        sys.exit(1)

    # TF version info (non-fatal — SageMaker container version may differ from local)
    try:
        import tensorflow as tf
        tf_ver = tf.__version__
        major_minor = ".".join(tf_ver.split(".")[:2])
        if major_minor != TF_FRAMEWORK_VERSION:
            print(
                f"  NOTE: Local TensorFlow is {tf_ver}. "
                f"The SageMaker container will use {TF_FRAMEWORK_VERSION}.x — this is expected."
            )
    except ImportError:
        pass

    print(f"  Python:      {sys.version.split()[0]}")
    try:
        import boto3 as _b
        print(f"  boto3:       {_b.__version__}")
    except Exception:
        pass
    try:
        import sagemaker as _sm
        print(f"  sagemaker:   {_sm.__version__}")
    except Exception:
        pass
    try:
        import tensorflow as _tf
        print(f"  tensorflow:  {_tf.__version__} (local)")
        print(f"  TF container:{TF_FRAMEWORK_VERSION}.x (SageMaker)")
    except Exception:
        pass


import boto3
import sagemaker
from sagemaker.tensorflow import TensorFlowModel
from botocore.exceptions import ClientError

# ─── Configuration ───────────────────────────────────────────────────
S3_BUCKET = os.getenv("SAGEMAKER_S3_BUCKET", "portfoliopulse-artifacts")
S3_MODEL_KEY = "models/model.tar.gz"
LOCAL_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "models",
    "neumf_model.keras",
)
SAGEMAKER_ROLE = os.getenv("SAGEMAKER_ROLE")  # IAM role ARN
ENDPOINT_NAME = "portfoliopulse-neumf"
TF_FRAMEWORK_VERSION = "2.19"   # Highest SageMaker container; native Keras 3
MEMORY_SIZE_MB = 3072
MAX_CONCURRENCY = 1

INFERENCE_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inference.py")


def package_model(model_path: str, inference_script: str) -> str:
    """
    Create model.tar.gz with the structure SageMaker TF Serving expects:
        1/                  <- versioned SavedModel (required by TF Serving)
            saved_model.pb
            variables/
        code/
            inference.py    <- pre/post-processing hooks
    Returns path to the tar.gz file.
    """
    if not os.path.exists(model_path):
        print(f"ERROR: Model not found at {model_path}")
        print("Either place neumf_model.keras in the models/ directory,")
        print("or download it from S3:")
        print(f"    aws s3 cp s3://{S3_BUCKET}/models/neumf_model.keras {model_path}")
        sys.exit(1)

    import tensorflow as tf

    tmp_dir = tempfile.mkdtemp()
    tar_path = os.path.join(tmp_dir, "model.tar.gz")

    print("  Loading .keras model and exporting SavedModel ...")
    saved_model_dir = os.path.join(tmp_dir, "1")
    model = tf.keras.models.load_model(model_path)
    model.export(saved_model_dir)

    loaded = tf.saved_model.load(saved_model_dir)
    sig = loaded.signatures["serving_default"]
    input_names = list(sig.structured_input_signature[1].keys())
    print(f"  SavedModel input tensors: {input_names}")
    print(f"  SavedModel output tensors: {list(sig.structured_outputs.keys())}")

    code_dir = os.path.join(tmp_dir, "code")
    os.makedirs(code_dir)
    shutil.copy2(inference_script, os.path.join(code_dir, "inference.py"))

    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(saved_model_dir, arcname="1")
        tar.add(code_dir, arcname="code")

    size_mb = os.path.getsize(tar_path) / (1024 * 1024)
    print(f"  Packaged model.tar.gz ({size_mb:.1f} MB)")
    print("  Included artifacts:")
    print("    - 1/ (SavedModel for TF Serving)")
    print("    - code/inference.py")
    return tar_path


def upload_to_s3(tar_path: str) -> str:
    """Upload model.tar.gz to S3 and return the S3 URI."""
    s3 = boto3.client("s3")
    s3_uri = f"s3://{S3_BUCKET}/{S3_MODEL_KEY}"
    print(f"Uploading to {s3_uri} ...")
    s3.upload_file(tar_path, S3_BUCKET, S3_MODEL_KEY)
    print("Upload complete.")
    return s3_uri


def cleanup_existing_endpoint():
    """
    If a failed endpoint/config already exists with the same name, delete it
    so a fresh deploy can recreate the resources cleanly.
    """
    sm = boto3.client("sagemaker")

    try:
        resp = sm.describe_endpoint(EndpointName=ENDPOINT_NAME)
        status = resp["EndpointStatus"]
        print(f"Found existing endpoint '{ENDPOINT_NAME}' with status: {status}")
        print("Deleting existing endpoint ...")
        sm.delete_endpoint(EndpointName=ENDPOINT_NAME)

        waiter = sm.get_waiter("endpoint_deleted")
        waiter.wait(EndpointName=ENDPOINT_NAME)
        print("Endpoint deleted.")
    except ClientError as e:
        if "Could not find endpoint" not in str(e):
            raise

    try:
        print("Deleting existing endpoint config ...")
        sm.delete_endpoint_config(EndpointConfigName=ENDPOINT_NAME)
        print("Endpoint config deleted.")
    except ClientError as e:
        if "Could not find endpoint configuration" not in str(e):
            raise


def deploy_endpoint(model_data_uri: str) -> str:
    """Deploy the model as a SageMaker Serverless Inference endpoint."""
    if not SAGEMAKER_ROLE:
        print("ERROR: Set the SAGEMAKER_ROLE environment variable to your")
        print("SageMaker execution role ARN. Example:")
        print("    set SAGEMAKER_ROLE=arn:aws:iam::123456789012:role/SageMakerExecutionRole")
        sys.exit(1)

    print(f"Creating TensorFlowModel pointing to {model_data_uri} ...")

    tf_model = TensorFlowModel(
        model_data=model_data_uri,
        role=SAGEMAKER_ROLE,
        framework_version=TF_FRAMEWORK_VERSION,
    )

    serverless_config = sagemaker.serverless.ServerlessInferenceConfig(
        memory_size_in_mb=MEMORY_SIZE_MB,
        max_concurrency=MAX_CONCURRENCY,
    )

    cleanup_existing_endpoint()

    print(f"Deploying serverless endpoint '{ENDPOINT_NAME}' ...")
    print(f"  Memory:      {MEMORY_SIZE_MB} MB")
    print("  Concurrency: 1")
    print("  This may take 3-5 minutes ...")

    predictor = tf_model.deploy(
        endpoint_name=ENDPOINT_NAME,
        serverless_inference_config=serverless_config,
    )

    print(f"\nEndpoint deployed: {ENDPOINT_NAME}")
    print(f"Endpoint ARN:      {predictor.endpoint_name}")
    return predictor.endpoint_name


def main():
    print("=" * 60)
    print("  PortfolioPulse — SageMaker Deployment")
    print("=" * 60)

    print("\n[0/3] Preflight environment check ...")
    _preflight_check()
    print("  All checks passed.\n")

    # Step 1: Package
    print("\n[1/3] Packaging model ...")
    tar_path = package_model(LOCAL_MODEL_PATH, INFERENCE_SCRIPT)

    # Step 2: Upload
    print("\n[2/3] Uploading to S3 ...")
    s3_uri = upload_to_s3(tar_path)

    # Step 3: Deploy
    print("\n[3/3] Deploying SageMaker Serverless Endpoint ...")
    endpoint = deploy_endpoint(s3_uri)

    # Cleanup
    shutil.rmtree(os.path.dirname(tar_path), ignore_errors=True)

    print("\n" + "=" * 60)
    print("  Deployment complete!")
    print(f"  Endpoint name: {endpoint}")
    print()
    print("  Test it with:")
    print("    python -m sm_endpoint.test_endpoint")
    print()
    print("  Add this to your .env:")
    print(f"    SAGEMAKER_ENDPOINT={endpoint}")
    print("=" * 60)


if __name__ == "__main__":
    main()
