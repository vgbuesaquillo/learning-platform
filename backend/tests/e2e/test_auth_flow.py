import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.security import create_access_token
from datetime import timedelta
import json

# Assuming conftest.py provides fixtures like 'client', 'student_token', 'instructor_token', 'db_session'
# and ensures the app context is set up correctly.

# ── Test Authentication Flow ──
def test_register_and_login_returns_token(client: TestClient):
    """Tests user registration and successful login, returning an access token."""
    register_response = client.post("/api/v1/auth/register", json={
        "email": "testuser@example.com",
        "full_name": "Test User",
        "password": "securepassword123"
    })
    assert register_response.status_code == 201 # Assuming 201 for successful creation

    login_response = client.post("/api/v1/auth/login", json={
        "email": "testuser@example.com",
        "password": "securepassword123"
    })
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()
    assert "token_type" in login_response.json()
    assert login_response.json()["token_type"] == "bearer"

def test_login_with_wrong_password_returns_401(client: TestClient):
    """Tests that login fails with an incorrect password."""
    client.post("/api/v1/auth/register", json={
        "email": "testuser@example.com",
        "full_name": "Test User",
        "password": "securepassword123"
    }) # Register first
    response = client.post("/api/v1/auth/login", json={
        "email": "testuser@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401 # Assuming 401 for invalid credentials
    assert "detail" in response.json()
    # Check for a specific error message if the API provides one (e.g., "Incorrect email or password")

def test_me_endpoint_requires_auth(client: TestClient):
    """Tests that the /auth/me endpoint requires authentication."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401 # Expecting unauthorized

def test_me_returns_current_user_data(client: TestClient, student_token: str):
    """Tests that /auth/me returns the correct user details with a valid token."""
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {student_token}"})
    assert response.status_code == 200
    user_data = response.json()
    assert "email" in user_data
    assert "full_name" in user_data
    assert "id" in user_data
    # Add checks for specific fields if known, e.g., email should match the token's subject

def test_duplicate_email_registration_returns_400(client: TestClient):
    """Tests that registering with an existing email returns a 400 error."""
    client.post("/api/v1/auth/register", json={
        "email": "duplicate@example.com",
        "full_name": "First User",
        "password": "password123"
    }) # First registration
    response = client.post("/api/v1/auth/register", json={
        "email": "duplicate@example.com",
        "full_name": "Second User",
        "password": "anotherpassword"
    }) # Second registration with same email
    assert response.status_code == 400 # Assuming 400 for bad request/conflict
    assert "detail" in response.json()
    # Assert specific error message if available, e.g., "Email already registered"

# Note: Actual token generation logic might need to be integrated if not provided by fixtures.
# For student_token and instructor_token fixtures, ensure they are properly generated
# and associated with users that have the correct roles (student, instructor).
