"""Dashboard — real-time VPC-Stream monitoring UI with WebSocket alerts."""
import logging
import os
import sys
import threading
from collections import deque

import requests as http_req
import socketio as sio_client
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

REQUIRED = ["DASHBOARD_PORT", "ANOMALY_DETECTOR_WS_URL", "LOG_GENERATOR_URL",
            "INTERNAL_TOKEN"]
for var in REQUIRED:
    if not os.environ.get(var):
        log.error("Missing required env var: %s — exiting.", var)
        sys.exit(1)

PORT = int(os.environ.get("DASHBOARD_PORT"))
DETECTOR_WS = os.environ.get("ANOMALY_DETECTOR_WS_URL")
GENERATOR_URL = os.environ.get("LOG_GENERATOR_URL").rstrip("/")
TOKEN = os.environ.get("INTERNAL_TOKEN")

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
alerts = deque(maxlen=100)

# --- Background SocketIO client connecting to Anomaly Detector ---
bg_sio = sio_client.Client(reconnection=True, reconnection_delay=2)

@bg_sio.on("alert")
def _on_alert(data):
    """Receive alert from Anomaly Detector and relay to browser clients."""
    alerts.appendleft(data)
    socketio.emit("alert", data)
    log.info("Alert relayed: %s", data.get("type"))

@bg_sio.on("flow")
def _on_flow(data):
    """Receive flow event from Anomaly Detector and relay to browsers."""
    socketio.emit("flow", data)

def _connect_upstream():
    """Connect to Anomaly Detector WebSocket in background thread."""
    try:
        log.info("Connecting to Anomaly Detector WS at %s …", DETECTOR_WS)
        bg_sio.connect(DETECTOR_WS, wait_timeout=10)
    except Exception:
        log.exception("Failed to connect to Anomaly Detector WS")

threading.Thread(target=_connect_upstream, daemon=True).start()

# --- Helpers ---
_HDR = {"X-Internal-Token": TOKEN}

def _proxy_get(path):
    """Proxy a GET request to the Log Generator."""
    r = http_req.get(f"{GENERATOR_URL}{path}", headers=_HDR, timeout=5)
    return jsonify(r.json()), r.status_code

def _proxy_post(path, body=None):
    """Proxy a POST request to the Log Generator."""
    r = http_req.post(f"{GENERATOR_URL}{path}", json=body, headers=_HDR, timeout=5)
    return jsonify(r.json()), r.status_code

# --- Security & routes ---
@app.after_request
def _security_headers(resp):
    """Attach security headers to every response."""
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["X-XSS-Protection"] = "1; mode=block"
    return resp

@app.route("/")
def index():
    """Serve the monitoring dashboard."""
    return render_template("index.html")

@app.route("/health")
def health():
    """Liveness probe — always returns ok."""
    return jsonify(status="ok")

@app.route("/control/start", methods=["POST"])
def ctrl_start():
    """Proxy start command to Log Generator."""
    try:
        return _proxy_get("/start")
    except Exception:
        log.exception("Error proxying /start")
        return jsonify(error="Internal server error"), 500

@app.route("/control/stop", methods=["POST"])
def ctrl_stop():
    """Proxy stop command to Log Generator."""
    try:
        return _proxy_get("/stop")
    except Exception:
        log.exception("Error proxying /stop")
        return jsonify(error="Internal server error"), 500

@app.route("/control/rate", methods=["POST"])
def ctrl_rate():
    """Proxy rate change to Log Generator."""
    try:
        data = request.get_json(silent=True) or {}
        return _proxy_post("/rate", data)
    except Exception:
        log.exception("Error proxying /rate")
        return jsonify(error="Internal server error"), 500

@app.route("/alerts")
def get_alerts():
    """Return recent alerts as JSON."""
    try:
        return jsonify(list(alerts))
    except Exception:
        log.exception("Error in /alerts")
        return jsonify(error="Internal server error"), 500

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=PORT)
