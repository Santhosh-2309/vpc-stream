"""Tests for Dashboard microservice."""
import os
import sys
from unittest.mock import patch, MagicMock
import pytest

# Env defaults ensuring full stability dynamically across system constraints
os.environ["DASHBOARD_PORT"] = "5003"
os.environ["ANOMALY_DETECTOR_WS_URL"] = "http://localhost:5002"
os.environ["LOG_GENERATOR_URL"] = "http://localhost:5001"
os.environ["INTERNAL_TOKEN"] = "test-token-123"

# Mask background SocketIO connectivity strictly before imports
patch("socketio.Client.connect").start()
patch("socketio.Client.start_background_task").start()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.modules.pop("app", None)
from app import app

@pytest.fixture
def client():
    """Flask UI core backend injection endpoint fixture wrapper."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_health_returns_200(client):
    """Test GET /health validates baseline health routing responses completely intact."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json == {"status": "ok"}

def test_health_has_security_headers(client):
    """Test core global application headers persist throughout generic /health hooks securely."""
    res = client.get("/health")
    assert "X-Content-Type-Options" in res.headers
    assert res.headers["X-Content-Type-Options"] == "nosniff"

def test_index_returns_200(client):
    """Test GET / standardizes layout template render without breaking contexts silently."""
    res = client.get("/")
    assert res.status_code == 200

def test_index_contains_dashboard_title(client):
    """Test dynamic UI layout retains required textual elements structurally."""
    res = client.get("/")
    assert b"vpc-stream" in res.data.lower()

@patch("app.http_req")
def test_control_start_proxies_request(mock_session, client):
    """Test POST /control/start proxies to log generator."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"message": "started"}
    mock_session.get.return_value = mock_response
    
    res = client.post("/control/start")
    assert res.status_code == 200
    mock_session.get.assert_called_once()

@patch("app.http_req")
def test_control_stop_proxies_request(mock_session, client):
    """Test POST /control/stop proxies to log generator."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"message": "stopped"}
    mock_session.get.return_value = mock_response
    
    res = client.post("/control/stop")
    assert res.status_code == 200
    mock_session.get.assert_called_once()

@patch("requests.post")
def test_control_rate_proxies_request(mock_post, client):
    """Test POST /control/rate enforces mapping against specified payload integers explicitly."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"message": "updated"}
    
    res = client.post("/control/rate", json={"rate": 100})
    assert res.status_code == 200
    mock_post.assert_called_once()
    assert "http://localhost:5001/rate" in mock_post.call_args[0][0]
    assert mock_post.call_args[1]["json"] == {"rate": 100}
