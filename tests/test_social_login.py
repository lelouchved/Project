import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_social_login_google():
    res = client.post("/api/auth/social-login", json={"provider": "google"})
    assert res.status_code == 200
    data = res.json()
    assert "Google" in data["message"]
    assert "access_token" in data
    assert data["user"]["role"] == "STUDENT"

def test_social_login_instagram():
    res = client.post("/api/auth/social-login", json={"provider": "instagram"})
    assert res.status_code == 200
    data = res.json()
    assert "Instagram" in data["message"]
    assert "access_token" in data

def test_social_login_github():
    res = client.post("/api/auth/social-login", json={"provider": "github"})
    assert res.status_code == 200
    data = res.json()
    assert "Github" in data["message"]
    assert "access_token" in data

def test_social_login_invalid_provider():
    res = client.post("/api/auth/social-login", json={"provider": "unsupported_provider"})
    assert res.status_code == 400
    assert "Unsupported social provider" in res.json()["detail"]
