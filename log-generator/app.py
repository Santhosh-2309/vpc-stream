"""Log Generator — streams CICIDS2017 rows as AWS VPC Flow Logs."""
import logging
import os
import sys
import threading
import time

import pandas as pd
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

REQUIRED = ["LOG_GENERATOR_PORT", "CICIDS2017_PATH", "ANOMALY_DETECTOR_URL",
            "INTERNAL_TOKEN", "LOG_RATE_LIMIT"]
for var in REQUIRED:
    if not os.environ.get(var):
        log.error("Missing required env var: %s — exiting.", var)
        sys.exit(1)

PORT = int(os.environ.get("LOG_GENERATOR_PORT"))
CSV_PATH = os.environ.get("CICIDS2017_PATH")
DETECTOR_URL = os.environ.get("ANOMALY_DETECTOR_URL")
TOKEN = os.environ.get("INTERNAL_TOKEN")
RATE_LIMIT = os.environ.get("LOG_RATE_LIMIT", "10 per minute")

app = Flask(__name__)
limiter = Limiter(get_remote_address, app=app, default_limits=[])

log.info("Loading CICIDS2017 dataset from %s …", CSV_PATH)
df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
df.columns = df.columns.str.strip()
log.info("Loaded %d rows, %d columns.", len(df), len(df.columns))

streaming = False
rate_rps = 10
_thread = None

def _safe_int(val, default):
    try:
        f = float(val)
        import math
        return default if (math.isinf(f) or math.isnan(f)) else int(f)
    except Exception:
        return default

def _to_vpc_log(row, idx):
    """Map a CICIDS2017 row to an AWS VPC Flow Log dict."""
    dport = int(row["Destination Port"])

    remainder = idx % 10
    if remainder < 7:
        srcaddr = "10.0.1.1"
    elif remainder < 9:
        srcaddr = "10.0.0.5"
    else:
        srcaddr = f"10.0.2.{idx % 256}"

    dst_pool = [f"10.1.0.{i}" for i in range(1, 21)]
    dstaddr = dst_pool[idx % 20]

    return {
        "srcaddr": srcaddr,
        "dstaddr": dstaddr,
        "dstport": dport,
        "protocol": 6 if int(row.get("SYN Flag Count", 0)) > 0 else 17,
        "packets": max(1, _safe_int(row.get("Flow Packets/s", 1), 1)),
        "bytes": max(0, _safe_int(row.get("Flow Bytes/s", 0), 0)),
        "action": "ACCEPT" if str(row.get("Label", "")).strip() == "BENIGN" else "REJECT",
    }

def _stream_logs():
    """Background worker — iterates CSV rows, POSTs each as a VPC log."""
    global streaming
    headers = {"X-Internal-Token": TOKEN, "Content-Type": "application/json"}
    url = f"{DETECTOR_URL.rstrip('/')}/log"
    idx = 0
    while streaming and idx < len(df):
        try:
            requests.post(url, json=_to_vpc_log(df.iloc[idx], idx),
                          headers=headers, timeout=5)
        except requests.RequestException as e:
            logging.error(f"Failed to POST log to anomaly detector: {e}")
            log.warning("POST failed (row %d): %s", idx, e)
        idx += 1
        time.sleep(1.0 / rate_rps)
    streaming = False
    log.info("Streaming stopped at row %d.", idx)

@app.after_request
def _security_headers(resp):
    """Attach security headers to every response."""
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["X-XSS-Protection"] = "1; mode=block"
    return resp

@app.route("/health")
def health():
    """Liveness probe — always returns ok."""
    return jsonify(status="ok")

@app.route("/start")
@limiter.limit(f"{os.environ.get('LOG_RATE_LIMIT', '10')} per minute")
def start():
    """Begin streaming CSV rows to the anomaly detector."""
    global streaming, _thread
    try:
        if streaming:
            return jsonify(message="Already streaming"), 200
        streaming = True
        _thread = threading.Thread(target=_stream_logs, daemon=True)
        _thread.start()
        log.info("Streaming started at %d rows/s.", rate_rps)
        return jsonify(message="Streaming started", rate=rate_rps)
    except Exception:
        log.exception("Error in /start")
        return jsonify(error="Internal server error"), 500

@app.route("/stop")
@limiter.limit(f"{os.environ.get('LOG_RATE_LIMIT', '10')} per minute")
def stop():
    """Stop the streaming background thread."""
    global streaming
    try:
        streaming = False
        log.info("Streaming stop requested.")
        return jsonify(message="Streaming stopped")
    except Exception:
        log.exception("Error in /stop")
        return jsonify(error="Internal server error"), 500

@app.route("/rate", methods=["POST"])
@limiter.limit(f"{os.environ.get('LOG_RATE_LIMIT', '10')} per minute")
def set_rate():
    """Set streaming speed in rows per second (1–1000)."""
    global rate_rps
    try:
        data = request.get_json(silent=True) or {}
        new_rate = data.get("rate")
        if not isinstance(new_rate, int) or not 1 <= new_rate <= 1000:
            log.warning("Invalid rate input: %s", new_rate)
            return jsonify(error="rate must be int between 1 and 1000"), 400
        rate_rps = new_rate
        log.info("Rate updated to %d rows/s.", rate_rps)
        return jsonify(message="Rate updated", rate=rate_rps)
    except Exception:
        log.exception("Error in /rate")
        return jsonify(error="Internal server error"), 500

@app.route("/status")
@limiter.limit(f"{os.environ.get('LOG_RATE_LIMIT', '10')} per minute")
def status():
    """Return current streaming state and rate."""
    try:
        return jsonify(streaming=streaming, rate=rate_rps, total_rows=len(df))
    except Exception:
        log.exception("Error in /status")
        return jsonify(error="Internal server error"), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
