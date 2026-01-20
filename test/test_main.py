"""Tests pour le module main.py"""
import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client):
    """Teste l'endpoint racine."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_docs_endpoint(client):
    """Teste que la documentation est accessible."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_endpoint(client):
    """Teste que l'OpenAPI schema est accessible."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data


def test_health_endpoint(client):
    """Teste l'endpoint de santé."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "model_loaded" in data
