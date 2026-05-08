import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.security import create_access_token
from datetime import timedelta
import json
from uuid import UUID as UUIDType # Import UUIDType for consistency

# Assuming conftest.py provides fixtures like 'client', 'student_token', 'instructor_token', 'db_session'
# and ensures the app context is set up correctly.

# --- Test Authentication Flow ---
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
    # Assuming a specific error detail for incorrect credentials
    assert "Incorrect email or password" in response.json()["detail"]

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

def test_token_expiration(client: TestClient, student_token: str):
    """Tests if the access token expires and becomes invalid."""
    # NOTE: This test requires manipulating token validity or mocking it, which is complex in E2E.
    # For now, this is a placeholder. A proper test would involve:
    # 1. Creating a token with a very short expiry.
    # 2. Waiting for it to expire.
    # 3. Attempting to use it.
    pass # Placeholder for token expiration test

def test_logout_invalidates_token(client: TestClient, student_token: str):
    """Tests if logging out invalidates the token."""
    # NOTE: This test requires a logout endpoint and token invalidation logic (e.g., blacklist).
    # If a logout endpoint exists, e.g., POST /api/v1/auth/logout:
    # logout_response = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {student_token}"})
    # assert logout_response.status_code == 200 # Or 204, etc.
    #
    # After logout, attempting to use the token should fail.
    # response_after_logout = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {student_token}"})
    # assert response_after_logout.status_code == 401 # Expecting unauthorized
    #
    # Since logout endpoint and logic are not confirmed, this is a placeholder.
    pass # Placeholder for logout test

def test_password_policy_on_registration(client: TestClient):
    """Tests that registration enforces basic password policies."""
    # Example: Password too short
    response_short_pass = client.post("/api/v1/auth/register", json={
        "email": "shortpass@example.com",
        "full_name": "Short Pass User",
        "password": "123" # Too short
    })
    assert response_short_pass.status_code == 400 # Expecting bad request
    # Assert that the error detail indicates the password is too short
    assert "Password is too short" in response_short_pass.json().get("detail", "")

    # Example: Missing password complexity (if any enforced, e.g., number, uppercase)
    # This depends on the actual backend validation logic.
    # response_no_complexity = client.post("/api/v1/auth/register", json={
    #     "email": "nocomplexity@example.com",
    #     "full_name": "No Complexity User",
    #     "password": "password" # Lacks complexity if enforced
    # })
    # # Assert based on expected behavior (e.g., 400 if policy not met)
    # # assert response_no_complexity.status_code == 400
    # # assert "Password does not meet complexity requirements" in response_no_complexity.json().get("detail", "")

    pass # Placeholder for more detailed password policy tests

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
    assert "El email ya está registrado" in response.json()["detail"] # Specific message from backend/api/auth.py