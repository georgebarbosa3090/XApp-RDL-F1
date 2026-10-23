import pytest
from src.observability.health_server import HealthServer, AppState, HAS_FASTAPI

def test_health_server_state_management():
    server = HealthServer(host="127.0.0.1", port=9099)
    assert server.state == AppState.STARTING
    
    server.set_state(AppState.READY)
    assert server.state == AppState.READY
    
    server.set_state(AppState.DEGRADED)
    assert server.state == AppState.DEGRADED

def test_health_server_endpoints():
    if not HAS_FASTAPI:
        pytest.skip("FastAPI not installed in environment")
        
    from fastapi.testclient import TestClient
    
    server = HealthServer(host="127.0.0.1", port=9099)
    client = TestClient(server.app)
    
    # 1. /health
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "UP"
    assert "uptime_seconds" in data
    
    # 2. /ready in STARTING (must return 503)
    server.set_state(AppState.STARTING)
    r = client.get("/ready")
    assert r.status_code == 503
    assert r.json()["status"] == "NOT_READY"
    
    # 3. /ready in READY (must return 200)
    server.set_state(AppState.READY)
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.json()["status"] == "READY"
    
    # 4. /ready in DEGRADED (must return 200)
    server.set_state(AppState.DEGRADED)
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.json()["status"] == "READY"
    
    # 5. /status
    r = client.get("/status")
    assert r.status_code == 200
    sdata = r.json()
    assert sdata["state"] == AppState.DEGRADED
    assert sdata["version"] == "1.1.0"

def test_health_server_fallback_and_run():
    server = HealthServer(host="127.0.0.1", port=9099)
    server.run()
    assert server.state == AppState.STARTING
    from src.observability.health_server import Response, status
    resp = Response(status_code=503)
    assert resp.status_code == 503
    assert status.HTTP_200_OK == 200
    assert status.HTTP_503_SERVICE_UNAVAILABLE == 503

