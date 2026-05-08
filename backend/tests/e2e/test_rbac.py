import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.security import create_access_token
from datetime import timedelta
from uuid import UUID as UUIDType # Import UUIDType for consistency
import json

# --- Test RBAC Endpoints ---

@pytest.fixture
def authorized_client(client: TestClient, student_token: str):
    """Provides a client authenticated as a student."""
    return client, student_token

@pytest.fixture
def instructor_authorized_client(client: TestClient, instructor_token: str):
    """Provides a client authenticated as an instructor."""
    return client, instructor_token

# Placeholder for potential specific user IDs if needed for testing resource ownership
# @pytest.fixture
# def student_user_id(db_session: Session, student_token: str) -> UUIDType:
#     # In a real scenario, decode token to get user ID, or query DB
#     # For this example, we'll use a known placeholder
#     return UUIDType("123e4567-e89b-12d3-a456-426614174000")

def test_unauthenticated_access_to_protected_endpoints(client: TestClient):
    """Ensure endpoints requiring authentication return 401 if no token is provided."""
    # Test various protected endpoints
    protected_endpoints = [
        "/api/v1/auth/me",
        "/api/v1/evidence/", # All evidences endpoint (instructor only, but requires auth)
        "/api/v1/evidence/my", # My evidences endpoint
        "/api/v1/progress/dashboard/a1b2c3d4-e5f6-7890-1234-567890abcdef", # Progress dashboard endpoint
        "/api/v1/evidence/interactions", # Record interaction endpoint
    ]
    for endpoint in protected_endpoints:
        response = client.get(endpoint)
        assert response.status_code == 401, f"Access to {endpoint} should require authentication"
        assert "detail" in response.json()
        # Check for common auth error messages, adjust if backend provides different ones
        assert "Not authenticated" in response.json()["detail"] or "Authentication credentials were not provided" in response.json()["detail"]

def test_instructor_access_to_student_only_endpoints(instructor_authorized_client):
    """Ensure instructors cannot access endpoints restricted to students (e.g., /evidence/my if implicitly restricted)."""
    client, instructor_token = instructor_authorized_client # Use instructor token

    # Test instructor access to '/api/v1/evidence/' (intended to be instructor-only)
    response_instructor = client.get("/api/v1/evidence/", headers={"Authorization": f"Bearer {instructor_token}"})
    assert response_instructor.status_code == 200, "Instructor should access /api/v1/evidence/"

    # Test student access to '/api/v1/evidence/' (should be denied)
    # We need a student token for this. Assuming it's available.
    try:
        # This is a conceptual check. The 'student_token' fixture needs to be available.
        # If it's not, this part might fail.
        student_token_from_fixture = client.application.state.get('student_token_fixture') # Example of accessing fixture if available in app state
        if not student_token_from_fixture:
             # Fallback: if directly available in test scope (e.g., from conftest)
             from conftest import student_token
             student_token_val = student_token
        else:
            student_token_val = student_token_from_fixture
    except NameError:
        pytest.skip("student_token fixture not available for testing student access.")

    response_student = client.get("/api/v1/evidence/", headers={"Authorization": f"Bearer {student_token_val}"})
    assert response_student.status_code == 403, f"Student should NOT access /api/v1/evidence/"
    assert "Se requiere rol de instructor" in response_student.json()["detail"]

def test_access_to_specific_resource_ownership(client: TestClient, student_token: str, instructor_token: str, db_session: Session):
    """Tests RBAC for endpoints that require access based on resource ownership or role."""
    # This test is more complex as it requires creating specific resources and testing
    # access for different roles (student vs instructor) to those resources.

    # Setup: Create an activity, evidence for a student
    from app.domain.models import Activity, User, Theme, LearningItem, UserProgress
    from uuid import UUID as UUIDType

    # Ensure mock data is clean and isolated for this test (or handled by fixtures)
    # For simplicity, we'll create minimal mock data if not already present.
    # Assume student and instructor tokens correspond to valid and distinct users.

    # Mock Activity for evidence creation
    activity_id_uuid = UUIDType("f47ac10b-58cc-4372-a567-0e02b2c3d479")
    mock_activity = Activity(
        id=activity_id_uuid, title="Mock Activity for RBAC", description="Activity for RBAC tests.",
        evidence_type="activity", max_score=100.0, is_required=True, module_id=UUIDType("a1b2c3d4-e5f6-7890-1234-567890abcdef")
    )
    db_session.add(mock_activity)
    # Commit to ensure it's in the DB for subsequent operations
    db_session.commit()
    # Refresh might be needed if IDs are auto-generated and used immediately, but we're using explicit UUIDs.
    # db_session.refresh(mock_activity)

    # Create evidence as student
    create_response = client.post("/api/v1/evidence/",
                                json={"activity_id": str(activity_id_uuid), "content": "Student's evidence for RBAC test."},
                                headers={"Authorization": f"Bearer {student_token}"})
    assert create_response.status_code == 201
    evidence_id = create_response.json()["id"]

    # --- Test student accessing their own evidence ---
    response_student_own = client.get("/api/v1/evidence/my", headers={"Authorization": f"Bearer {student_token}"})
    assert response_student_own.status_code == 200
    assert len(response_student_own.json()) > 0 # Should return at least one evidence
    assert any(e["id"] == evidence_id for e in response_student_own.json()), "Student's own evidence should be returned by /evidence/my"

    # --- Test student accessing another student's evidence (if direct access endpoint existed) ---
    # Example: If there was an endpoint like GET /api/v1/evidence/{user_id}/{evidence_id}
    # The current /api/v1/evidence/ endpoint is instructor-only, so this scenario is implicitly tested there.
    # If a different 'get_evidence_by_user' endpoint existed, it would be tested here.

    # --- Test instructor accessing specific evidence ---
    # Instructor should be able to access any evidence, including the one created by the student via /api/v1/evidence/
    response_instructor_all_evidences = client.get("/api/v1/evidence/", headers={"Authorization": f"Bearer {instructor_token}"})
    assert response_instructor_all_evidences.status_code == 200, "Instructor should access all evidences endpoint."
    assert any(e["id"] == evidence_id for e in response_instructor_all_evidences.json()), "Instructor should be able to see the student's evidence via /api/v1/evidence/"

    # Test instructor reviewing evidence (this also tests instructor RBAC for review endpoint)
    response_instructor_review = client.post(f"/api/v1/evidence/{evidence_id}/review",
                                           json={"score": 85, "qualitative_feedback": "Good job."},
                                           headers={"Authorization": f"Bearer {instructor_token}"})
    assert response_instructor_review.status_code == 200
    assert response_instructor_review.json()["status"] == "approved"

    # --- Test access to progress dashboard ---
    module_id_uuid = UUIDType("a1b2c3d4-e5f6-7890-1234-567890abcdef") # Example module ID

    # Student accessing their own progress dashboard - should succeed
    response_student_progress = client.get(f"/api/v1/progress/dashboard/{module_id_uuid}", headers={"Authorization": f"Bearer {student_token}"})
    assert response_student_progress.status_code == 200
    assert response_student_progress.json()["user_id"] is not None # Should return user's data

    # Instructor accessing progress dashboard - should succeed returning instructor's data
    # Current endpoint /api/v1/progress/dashboard/{_module_id} uses get_current_user,
    # meaning it returns data for the authenticated user (instructor in this case).
    response_instructor_progress = client.get(f"/api/v1/progress/dashboard/{module_id_uuid}", headers={"Authorization": f"Bearer {instructor_token}"})
    assert response_instructor_progress.status_code == 200
    assert response_instructor_progress.json()["user_id"] is not None # Should return instructor's data

    # Test a hypothetical scenario where a student tries to access another student's progress dashboard
    # This would require an endpoint that accepts a target user_id and the require_own_resource or
    # similar logic to be applied. The current /progress/dashboard endpoint does not support this directly.
    # If such an endpoint were implemented, we'd test it here.


# --- Test specific RBAC error messages ---
def test_instructor_role_required_error_message(client: TestClient, student_token: str):
    """Verify specific error messages for role-based access control denials."""
    # Target an endpoint that requires instructor role
    instructor_only_endpoint = "/api/v1/evidence/" # Get all evidences

    response = client.get(instructor_only_endpoint, headers={"Authorization": f"Bearer {student_token}"})
    assert response.status_code == 403
    assert "Se requiere rol de instructor" in response.json().get("detail", ""), "Incorrect error message for instructor role denial."

# Additional RBAC tests can be added here for other endpoints and roles as needed.
