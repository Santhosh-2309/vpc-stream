"""Tests for Anomaly Detector microservice."""
import os
import sys
from unittest.mock import patch
import pytest

# Inject envs required for the module loading
os.environ["ANOMALY_DETECTOR_PORT"] = "5002"
os.environ["INTERNAL_TOKEN"] = "test-token-123"
os.environ["DDOS_THRESHOLD"] = "500"
os.environ["BLOCKED_IPS"] = "192.168.1.100,10.0.0.5"
os.environ["INFLUXDB_URL"] = "http://localhost:8086"
os.environ["INFLUXDB_TOKEN"] = "test-influx-token"
os.environ["INFLUXDB_ORG"] = "test_org"
os.environ["INFLUXDB_BUCKET"] = "test_bucket"

# Isolate InfluxDB connection
patch("influxdb_client.InfluxDBClient").start()

# Include app context path safely
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.modules.pop("app", None)
from app import app, _detect, _ddos_timestamps, _port_scan_data

@pytest.fixture
def client():
    """Flask test client fixture exposing internal logic context."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_health_returns_200(client):
    """Test GET /health returns robust status 200 and 'ok' json schema."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json == {"status": "ok"}

def test_log_rejected_without_token(client):
    """Test POST /log fails implicitly (401) without tracking token."""
    res = client.post("/log", json={"srcaddr": "1.1.1.1"})
    assert res.status_code == 401

def test_log_rejected_with_wrong_token(client):
    """Test POST /log gracefully fails responding to mismatched static token."""
    res = client.post("/log", headers={"X-Internal-Token": "wrong"}, json={})
    assert res.status_code == 401

def test_log_accepted_with_valid_token(client):
    """Test POST /log seamlessly returns 200 representing successful ingestion schema validation."""
    payload = {
        "srcaddr": "1.2.3.4", "dstaddr": "8.8.8.8", "dstport": 443,
        "protocol": 6, "packets": 10, "bytes": 500, "action": "ACCEPT"
    }
    with patch("app._write_anomaly"):
        with patch("app._write_log"):
            with patch("app._get_write_api", return_value=None):
                res = client.post("/log", headers={"X-Internal-Token": "test-token-123"}, json=payload)
    assert res.status_code == 200

def test_log_missing_fields_returns_400(client):
    """Test POST /log fails validating expected keys against incomplete POST body."""
    payload = {"srcaddr": "1.2.3.4"} # missing subset keys
    res = client.post("/log", headers={"X-Internal-Token": "test-token-123"}, json=payload)
    assert res.status_code == 400

def test_ddos_detection():
    """Test core logic evaluates and alerts DDos patterns correctly after thresholds breached."""
    # Reset temporal contexts effectively
    _ddos_timestamps.clear()
    entry = {"srcaddr": "2.2.2.2", "dstport": 80}
    
    anomalies = []
    # Trigger limit
    for _ in range(501):
        anomalies = _detect(entry)
        
    assert len(anomalies) > 0
    assert anomalies[0]["type"] == "DDoS"

def test_port_scan_detection():
    """Test port scan detection triggers with 6 unique ports."""
    from app import _check_port_scan, _port_scan_data
    
    # Clear existing state
    _port_scan_data.clear()
    
    src = "10.0.9.9"
    # Feed 6 unique ports from same source
    results = []
    for port in [80, 443, 22, 8080, 3306, 5432]:
        result = _check_port_scan(src, port)
        results.append(result)
    
    # After 6 unique ports, detection should trigger
    assert any(results), "Port scan should trigger after 6 unique ports"

def test_unauthorized_detection():
    """Test strict string matching captures blocked IP subset list inputs safely."""
    entry = {"srcaddr": "192.168.1.100", "dstport": 80}
    anomalies = _detect(entry)
    assert len(anomalies) > 0
    assert any(a["type"] == "Unauthorized" for a in anomalies)

def test_benign_traffic_no_anomaly():
    """Test isolated acceptable logic checks pass through completely unscathed vs defaults."""
    _ddos_timestamps.clear()
    _port_scan_data.clear()
    entry1 = {"srcaddr": "8.8.8.8", "dstport": 80}
    entry2 = {"srcaddr": "8.8.8.8", "dstport": 443}
    
    _detect(entry1)
    anomalies = _detect(entry2)
    assert len(anomalies) == 0
