"""Tests for the FastAPI server endpoints."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
# Find the server module - it might be in woodwind_designer/engine/ or backend/
try:
    from woodwind_designer.engine.design_server import app
except ImportError:
    try:
        from backend.main import app
    except ImportError:
        app = None

import pytest

@pytest.mark.skipif(app is None, reason="Server module not found")
class TestServerHealth:
    def test_health_endpoint(self):
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_presets_endpoint(self):
        client = TestClient(app)
        response = client.get("/presets")
        assert response.status_code == 200
        data = response.json()
        assert "presets" in data

    def test_optimize_presets(self):
        client = TestClient(app)
        response = client.get("/optimize/presets")
        assert response.status_code == 200
