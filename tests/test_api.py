import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "Industrial LLM Insight API" in response.json()["message"]

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200

def test_query_endpoint():
    response = client.post(
        "/query",
        json={"query": "pump temperature issues"}
    )
    assert response.status_code in [200, 503]  # 503 if RAG not initialized

def test_anomaly_endpoint():
    response = client.post(
        "/analyze_anomaly",
        json={
            "equipment_id": "pump_01",
            "anomaly_type": "temperature_spike"
        }
    )
    assert response.status_code in [200, 503]