import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

# --- Test RBAC Endpoints ---

def test_unauthenticated_access_to_protected_endpoints(client: TestClient, disable_auth):
    module_id = uuid4()
    protected_endpoints = [
        "/api/v1/auth/me",
        "/api/v1/evidence/",
        "/api/v1/evidence/my",
        f"/api/v1/progress/dashboard/{module_id}",
    ]
    for endpoint in protected_endpoints:
        response = client.get(endpoint)
        assert response.status_code == 401, f"Access to {endpoint} should require authentication"
        assert "detail" in response.json()

def test_instructor_access_to_all_evidences(client: TestClient, instructor_token: str):
    response = client.get("/api/v1/evidence/", headers={"Authorization": f"Bearer {instructor_token}"})
    assert response.status_code == 200

def test_student_cannot_access_instructor_endpoints(client: TestClient, student_token: str):
    response = client.get("/api/v1/evidence/", headers={"Authorization": f"Bearer {student_token}"})
    assert response.status_code == 403
    assert "Se requiere rol de instructor" in response.json()["detail"]

def test_access_to_specific_resource_ownership(client: TestClient, student_token: str, instructor_token: str, db_session: Session):
    from app.domain.models import Activity

    activity_id = uuid4()
    activity = Activity(
        id=activity_id, title="Mock Activity for RBAC", description="Activity for RBAC tests.",
        evidence_type="activity", max_score=100.0, is_required=True, module_id=uuid4()
    )
    db_session.add(activity)
    db_session.commit()

    create_response = client.post("/api/v1/evidence/",
                                json={"activity_id": str(activity_id), "content": "Student's evidence for RBAC test."},
                                headers={"Authorization": f"Bearer {student_token}"})
    assert create_response.status_code == 201
    evidence_id = create_response.json()["id"]

    response_student_own = client.get("/api/v1/evidence/my", headers={"Authorization": f"Bearer {student_token}"})
    assert response_student_own.status_code == 200
    assert len(response_student_own.json()) > 0
    assert any(e["id"] == evidence_id for e in response_student_own.json())

    response_instructor_all_evidences = client.get("/api/v1/evidence/", headers={"Authorization": f"Bearer {instructor_token}"})
    assert response_instructor_all_evidences.status_code == 200
    assert any(e["id"] == evidence_id for e in response_instructor_all_evidences.json())

    submit_response = client.post(f"/api/v1/evidence/{evidence_id}/submit",
                                  headers={"Authorization": f"Bearer {student_token}"})
    assert submit_response.status_code == 200

    response_instructor_review = client.post(f"/api/v1/evidence/{evidence_id}/review",
                                           json={"score": 85, "qualitative_feedback": "Good job."},
                                           headers={"Authorization": f"Bearer {instructor_token}"})
    assert response_instructor_review.status_code == 200
    assert response_instructor_review.json()["status"] == "approved"

    module_id = uuid4()
    response_student_progress = client.get(f"/api/v1/progress/dashboard/{module_id}", headers={"Authorization": f"Bearer {student_token}"})
    assert response_student_progress.status_code == 200
    assert response_student_progress.json()["user_id"] is not None

    response_instructor_progress = client.get(f"/api/v1/progress/dashboard/{module_id}", headers={"Authorization": f"Bearer {instructor_token}"})
    assert response_instructor_progress.status_code == 200
    assert response_instructor_progress.json()["user_id"] is not None

def test_instructor_role_required_error_message(client: TestClient, student_token: str):
    response = client.get("/api/v1/evidence/", headers={"Authorization": f"Bearer {student_token}"})
    assert response.status_code == 403
    assert "Se requiere rol de instructor" in response.json().get("detail", "")
