"""Anomaly Detector — inspects VPC Flow Logs for DDoS, PortScan, Unauthorized access."""
import logging
import os
import sys
from collections import defaultdict, deque
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_socketio import SocketIO
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

REQUIRED = ["ANOMALY_DETECTOR_PORT", "INTERNAL_TOKEN", "DDOS_THRESHOLD",
            "BLOCKED_IPS", "INFLUXDB_URL", "INFLUXDB_TOKEN", "INFLUXDB_ORG",
            "INFLUXDB_BUCKET"]
for var in REQUIRED:
    if not os.environ.get(var):
        log.error("Missing required env var: %s — exiting.", var)
        sys.exit(1)

PORT = int(os.environ.get("ANOMALY_DETECTOR_PORT"))
TOKEN = os.environ.get("INTERNAL_TOKEN")
DDOS_THRESH = int(os.environ.get("DDOS_THRESHOLD"))
BLOCKED = set(ip.strip() for ip in os.environ.get("BLOCKED_IPS", "").split(",") if ip.strip())

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

influx = InfluxDBClient(url=os.environ.get("INFLUXDB_URL"),
                        token=os.environ.get("INFLUXDB_TOKEN"), org=os.environ.get("INFLUXDB_ORG"))
write_api = influx.write_api(write_options=SYNCHRONOUS)
BUCKET = os.environ.get("INFLUXDB_BUCKET")

# In-memory state for anomaly detection
_req_times = defaultdict(list)   # srcaddr → [timestamps]
_port_hist = defaultdict(lambda: deque(maxlen=10))  # srcaddr → deque of dstports

LOG_FIELDS = ["srcaddr", "dstaddr", "dstport", "protocol", "packets", "bytes", "action"]


def _detect(entry):
    """Run all 3 anomaly checks and return list of anomaly dicts."""
    src = entry["srcaddr"]
    now = datetime.now(timezone.utc).timestamp()
    anomalies = []
    # 1. DDoS — request rate per srcaddr
    _req_times[src] = [t for t in _req_times[src] if now - t < 1.0]
    _req_times[src].append(now)
    if len(_req_times[src]) > DDOS_THRESH:
        anomalies.append({"type": "DDoS", "severity": "CRITICAL", "src_ip": src,
                          "detail": f"{len(_req_times[src])} req/s from {src}"})
    # 2. PortScan — sequential ports
    _port_hist[src].append(entry["dstport"])
    if len(_port_hist[src]) >= 5:
        last5 = list(_port_hist[src])[-5:]
        if last5 == list(range(last5[0], last5[0] + 5)):
            anomalies.append({"type": "PortScan", "severity": "WARNING", "src_ip": src,
                              "detail": f"Sequential ports {last5} from {src}"})
    # 3. Unauthorized — blocked IP
    if src in BLOCKED:
        anomalies.append({"type": "Unauthorized", "severity": "CRITICAL", "src_ip": src,
                          "detail": f"Blocked IP {src} attempted access"})
    return anomalies


def _write_log(entry):
    """Write a VPC Flow Log entry to InfluxDB."""
    p = (Point("vpc_logs")
         .tag("srcaddr", entry["srcaddr"]).tag("dstaddr", entry["dstaddr"])
         .tag("protocol", str(entry["protocol"]))
         .field("packets", entry["packets"]).field("bytes", entry["bytes"])
         .field("action", entry["action"]))
    write_api.write(bucket=BUCKET, record=p)


def _write_anomaly(a):
    """Write an anomaly event to InfluxDB and emit via WebSocket."""
    ts = datetime.now(timezone.utc).isoformat()
    p = (Point("anomaly_events")
         .tag("type", a["type"]).tag("severity", a["severity"]).tag("src_ip", a["src_ip"])
         .field("detail", a["detail"]))
    write_api.write(bucket=BUCKET, record=p)
    socketio.emit("alert", {**a, "timestamp": ts})
    log.warning("ANOMALY: %s | %s | %s", a["type"], a["severity"], a["detail"])


@app.before_request
def _check_token():
    """Validate X-Internal-Token on all routes except /health."""
    if request.path == "/health":
        return None
    if request.headers.get("X-Internal-Token") != TOKEN:
        log.warning("Unauthorized request to %s from %s", request.path, request.remote_addr)
        return jsonify(error="Unauthorized"), 401
    return None

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

@app.route("/log", methods=["POST"])
def receive_log():
    """Receive a VPC log, run anomaly detection, write to InfluxDB."""
    try:
        data = request.get_json(silent=True) or {}
        missing = [f for f in LOG_FIELDS if f not in data]
        if missing:
            log.warning("Invalid log payload — missing: %s", missing)
            return jsonify(error=f"Missing fields: {missing}"), 400
        entry = {f: data[f] for f in LOG_FIELDS}
        entry["dstport"] = int(entry["dstport"])
        entry["protocol"] = int(entry["protocol"])
        entry["packets"] = int(entry["packets"])
        entry["bytes"] = int(entry["bytes"])
        try:
            _write_log(entry)
        except Exception:
            log.exception("InfluxDB write failed for vpc_logs")

        socketio.emit('flow', {
            'srcaddr': entry['srcaddr'],
            'dstaddr': entry['dstaddr'],
            'protocol': entry['protocol'],
            'packets': entry['packets'],
            'bytes': entry['bytes'],
            'action': entry['action'],
            'timestamp': datetime.utcnow().isoformat()
        })

        for a in _detect(entry):
            try:
                _write_anomaly(a)
            except Exception:
                log.exception("InfluxDB write failed for anomaly_events")
        return jsonify(status="ok"), 200
    except Exception:
        log.exception("Error in /log")
        return jsonify(error="Internal server error"), 500

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=PORT)
