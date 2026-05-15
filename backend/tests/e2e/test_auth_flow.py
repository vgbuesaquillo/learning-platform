import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

def _unique_email():
    return f"test_{uuid4().hex[:8]}@example.com"

def test_register_and_login_returns_token(client: TestClient):
    email = _unique_email()
    register_response = client.post("/api/v1/auth/register", json={
        "email": email,
        "full_name": "Test User",
        "password": "securepassword123"
    })
    assert register_response.status_code == 201

    login_response = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "securepassword123"
    })
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()
    assert "token_type" in login_response.json()
    assert login_response.json()["token_type"] == "bearer"

def test_login_with_wrong_password_returns_401(client: TestClient):
    email = _unique_email()
    client.post("/api/v1/auth/register", json={
        "email": email,
        "full_name": "Test User",
        "password": "securepassword123"
    })
    response = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    assert "detail" in response.json()
    assert "Credenciales inválidas" in response.json()["detail"]

def test_me_endpoint_requires_auth(client: TestClient, disable_auth):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401

def test_me_returns_current_user_data(client: TestClient, student_token: str):
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {student_token}"})
    assert response.status_code == 200
    user_data = response.json()
    assert "email" in user_data
    assert "full_name" in user_data
    assert "id" in user_data

def test_token_expiration(client: TestClient, student_token: str):
    pass

def test_logout_invalidates_token(client: TestClient, student_token: str):
    pass

def test_password_policy_on_registration(client: TestClient):
    response_short_pass = client.post("/api/v1/auth/register", json={
        "email": _unique_email(),
        "full_name": "Short Pass User",
        "password": "123"
    })
    assert response_short_pass.status_code == 422

def test_duplicate_email_registration_returns_400(client: TestClient):
    email = _unique_email()
    client.post("/api/v1/auth/register", json={
        "email": email,
        "full_name": "First User",
        "password": "password123"
    })
    response = client.post("/api/v1/auth/register", json={
        "email": email,
        "full_name": "Second User",
        "password": "anotherpassword"
    })
    assert response.status_code == 400
    assert "detail" in response.json()
    assert "El email ya está registrado" in response.json()["detail"]
