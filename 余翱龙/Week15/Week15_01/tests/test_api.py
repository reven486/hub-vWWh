import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == 200
    assert "version" in response.json()


def test_health():
    """测试健康检查"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_chat_endpoint():
    """测试chat接口"""
    response = client.post(
        "/api/v1/chat",
        json={"query": "测试问题", "top_k": 2}
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data


def test_retrieve_endpoint():
    """测试retrieve接口"""
    response = client.post(
        "/api/v1/retrieve",
        json={"query": "测试查询", "top_k": 2}
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data