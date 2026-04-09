"""Tests for Log Generator microservice."""
import os
import sys
from unittest.mock import patch
import pandas as pd
import pytest

# Setup env vars before import
os.environ["LOG_GENERATOR_PORT"] = "5001"
os.environ["CICIDS2017_PATH"] = "./data/cicids2017.csv"
os.environ["ANOMALY_DETECTOR_URL"] = "http://localhost:5002"
os.environ["INTERNAL_TOKEN"] = "test-token-123"
os.environ["LOG_RATE_LIMIT"] = "1000 per minute"  # high to avoid 429 during tests

# Mock pandas read_csv globally before importing app
mock_df = pd.DataFrame({
    "Destination Port": [80, 443, 8080],
    "Flow Packets/s": [100, 200, 5000],
    "Flow Bytes/s": [1000, 2000, 50000],
    "SYN Flag Count": [1, 0, 1],
    "ACK Flag Count": [1, 1, 1],
    "Label": ["BENIGN", "BENIGN", "DDoS"]
})
patch('pandas.read_csv', return_value=mock_df).start()

# Mock threading so background task doesn't actually block/run
patch('threading.Thread.start').start()

# Add parent directory to sys module path for local imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.modules.pop("app", None)
from app import app

@pytest.fixture
def client():
    """Flask test client fixture."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_health_returns_200(client):
    """Test GET /health returns status 200 and explicit body."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json == {"status": "ok"}

def test_health_has_security_headers(client):
    """Test health response contains required security headers."""
    res = client.get("/health")
    assert "X-Content-Type-Options" in res.headers
    assert res.headers["X-Content-Type-Options"] == "nosniff"

def test_start_endpoint_exists(client):
    """Test GET /start routing exists and operates functionally."""
    res = client.get("/start")
    assert res.status_code in (200, 429)

def test_stop_endpoint_exists(client):
    """Test GET /stop routing exists and acts accordingly."""
    res = client.get("/stop")
    assert res.status_code in (200, 429)

def test_rate_valid_input(client):
    """Test POST /rate with valid integer accurately proxies/updates."""
    res = client.post("/rate", json={"rate": 50})
    assert res.status_code == 200

def test_rate_invalid_below_range(client):
    """Test POST /rate with rate < 1 safely returns 400."""
    res = client.post("/rate", json={"rate": 0})
    assert res.status_code == 400

def test_rate_invalid_above_range(client):
    """Test POST /rate with rate > 1000 cleanly errors out at 400."""
    res = client.post("/rate", json={"rate": 9999})
    assert res.status_code == 400

def test_rate_missing_field(client):
    """Test POST /rate with empty body falls back manually to 400."""
    res = client.post("/rate", json={})
    assert res.status_code == 400

def test_status_returns_json(client):
    """Test GET /status maps properly retaining JSON validity."""
    res = client.get("/status")
    assert res.status_code == 200
    assert "streaming" in res.json
