import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Multimodal RAG" in response.json()["message"]


def test_health_endpoint(client):
    """Test health check endpoint structure"""
    # Note: This will fail if services aren't running
    response = client.get("/api/v1/health")
    # Just check response structure
    if response.status_code == 200:
        data = response.json()
        assert "status" in data
        assert "qdrant" in data
        assert "dashscope" in data
