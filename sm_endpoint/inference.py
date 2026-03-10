"""
SageMaker TensorFlow Serving pre/post-processing handlers for PortfolioPulse.

These hooks run in the Python sidecar alongside TF Serving. TF Serving
loads the SavedModel from the 1/ directory; these handlers transform the
lightweight JSON API into TF Serving predict requests and back.

Avoids importing numpy — the sidecar image does not include it.
"""
import json

NUM_ITEMS = 3755
DEFAULT_TOP_N = 20
_LAST_TOP_N = DEFAULT_TOP_N


def _decode_request(data):
    if hasattr(data, "read"):
        raw = data.read()
    else:
        raw = data

    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")

    return json.loads(raw)


def input_handler(data, context):
    """
    Convert a lightweight request like:
        {"user_idx": 100, "top_n": 10}

    into a TensorFlow Serving predict payload. The SavedModel exported via
    model.export() uses the Keras input layer names `user_input` and `item_input`.
    """
    if context.request_content_type != "application/json":
        raise ValueError(f"Unsupported content type: {context.request_content_type}")

    global _LAST_TOP_N

    payload = _decode_request(data)
    user_idx = int(payload["user_idx"])
    _LAST_TOP_N = int(payload.get("top_n", DEFAULT_TOP_N))

    instances = []
    for item_idx in range(NUM_ITEMS):
        instances.append({
            "user_input": [float(user_idx)],
            "item_input": [float(item_idx)],
        })

    return json.dumps({
        "signature_name": "serving_default",
        "instances": instances,
    })


def output_handler(data, context):
    """
    Parse the TF Serving response, rank all scores, and return the
    top-N recommendations in the JSON shape expected by the app.
    """
    if data.status_code != 200:
        raise ValueError(data.content.decode("utf-8"))

    top_n = _LAST_TOP_N

    response = json.loads(data.content.decode("utf-8"))
    predictions = response.get("predictions", [])

    indexed = []
    for item_idx, pred in enumerate(predictions):
        if isinstance(pred, list):
            score = float(pred[0])
        else:
            score = float(pred)
        indexed.append((item_idx, score))

    indexed.sort(key=lambda x: x[1], reverse=True)

    body = json.dumps({
        "recommendations": [
            {"item_idx": idx, "score": round(score, 6)}
            for idx, score in indexed[:top_n]
        ]
    })

    accept = getattr(context, "accept_header", "application/json")
    return body, accept
