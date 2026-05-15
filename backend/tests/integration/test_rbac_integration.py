import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

def test_unauthenticated_access_to_protected_endpoints(client: TestClient, disable_auth):
    response = client.get("/api/v1/evidence/my")
    assert response.status_code == 401

def test_student_access_to_instructor_endpoint(client: TestClient, student_token: str):
    """Ensure a student cannot access endpoints requiring instructor role."""
    response = client.post(
        "/api/v1/evidence/some_evidence_id/review",
        json={"score": 80},
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Se requiere rol de instructor"

def test_student_access_to_all_evidences_endpoint(client: TestClient, student_token: str):
    response = client.get(
        "/api/v1/evidence/",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Se requiere rol de instructor"

def test_instructor_access_to_all_evidences_endpoint(client: TestClient, instructor_token: str):
    response = client.get(
        "/api/v1/evidence/",
        headers={"Authorization": f"Bearer {instructor_token}"}
    )
    assert response.status_code == 200

def test_student_access_to_own_evidence_only(client: TestClient, student_token: str, db_session: Session):
    response = client.get("/api/v1/evidence/my", headers={"Authorization": f"Bearer {student_token}"})
    assert response.status_code == 200

def test_student_cannot_access_other_user_progress_dashboard(client: TestClient, student_token: str, db_session: Session):
    module_id = uuid4()
    response = client.get(f"/api/v1/progress/dashboard/{module_id}", headers={"Authorization": f"Bearer {student_token}"})
    assert response.status_code == 200
