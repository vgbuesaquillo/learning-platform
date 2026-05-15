import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

def _unique_email():
    return f"user_{uuid4().hex[:8]}@example.com"

# --- Test Authentication Flow ---
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

# --- Test Evidence Flow (Create, Submit, Review) ---
def _create_activity(db_session: Session, module_id=None):
    from app.domain.models import Activity
    if module_id is None:
        module_id = uuid4()
    activity = Activity(
        id=uuid4(),
        title="Mock Activity",
        description="Mock activity for testing.",
        evidence_type="activity",
        rubric={"criteria": {"content": {"max_score": 100, "description": "Content quality"}}},
        max_score=100.0,
        is_required=True,
        module_id=module_id,
    )
    db_session.add(activity)
    db_session.commit()
    db_session.refresh(activity)
    return activity

def _create_theme(db_session: Session):
    from app.domain.models import Theme
    theme = Theme(
        id=uuid4(),
        name=f"Theme {uuid4().hex[:8]}",
        description="Mock theme.",
        order=1,
        is_active=True,
    )
    db_session.add(theme)
    db_session.commit()
    db_session.refresh(theme)
    return theme

def _create_learning_item(db_session: Session, theme_id):
    from app.domain.models import LearningItem
    item = LearningItem(
        id=uuid4(),
        theme_id=theme_id,
        item_type="concept",
        content=f"Learning item {uuid4().hex[:8]}",
        metadata={"difficulty": "intermediate"},
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item

def test_student_can_create_evidence(client: TestClient, student_token: str, db_session: Session):
    activity = _create_activity(db_session)
    response = client.post("/api/v1/evidence/",
                           json={
                               "activity_id": str(activity.id),
                               "content": "This is my evidence content.",
                               "reflection": "I learned a lot.",
                               "confidence_level": 4,
                           },
                           headers={"Authorization": f"Bearer {student_token}"})
    assert response.status_code == 201
    evidence_data = response.json()
    assert "id" in evidence_data
    assert evidence_data["content"] == "This is my evidence content."
    assert evidence_data["status"] == "draft"
    assert evidence_data["user_id"] is not None

def test_student_can_submit_evidence(client: TestClient, student_token: str, db_session: Session):
    activity = _create_activity(db_session)
    create_response = client.post("/api/v1/evidence/",
                                json={
                                    "activity_id": str(activity.id),
                                    "content": "This is my evidence content.",
                                },
                                headers={"Authorization": f"Bearer {student_token}"})
    assert create_response.status_code == 201
    evidence_id = create_response.json()["id"]

    submit_response = client.post(f"/api/v1/evidence/{evidence_id}/submit",
                                  headers={"Authorization": f"Bearer {student_token}"})
    assert submit_response.status_code == 200
    assert submit_response.json()["status"] == "submitted"
    assert "submitted_at" in submit_response.json()

def test_student_cannot_submit_already_submitted_evidence(client: TestClient, student_token: str, db_session: Session):
    activity = _create_activity(db_session)
    create_response = client.post("/api/v1/evidence/",
                                json={
                                    "activity_id": str(activity.id),
                                    "content": "Evidence content.",
                                },
                                headers={"Authorization": f"Bearer {student_token}"})
    assert create_response.status_code == 201
    evidence_id = create_response.json()["id"]

    client.post(f"/api/v1/evidence/{evidence_id}/submit", headers={"Authorization": f"Bearer {student_token}"})

    response = client.post(f"/api/v1/evidence/{evidence_id}/submit", headers={"Authorization": f"Bearer {student_token}"})
    assert response.status_code == 400
    assert "Only drafts can be submitted" in response.json()["detail"]

def test_instructor_can_review_evidence(client: TestClient, instructor_token: str, student_token: str, db_session: Session):
    module_id = uuid4()
    activity = _create_activity(db_session, module_id)
    theme = _create_theme(db_session)
    _create_learning_item(db_session, theme.id)

    create_response = client.post("/api/v1/evidence/",
                                json={
                                    "activity_id": str(activity.id),
                                    "content": "This evidence content about NLP and ML.",
                                    "reflection": "I feel confident about this.",
                                    "confidence_level": 4,
                                },
                                headers={"Authorization": f"Bearer {student_token}"})
    assert create_response.status_code == 201
    evidence_id = create_response.json()["id"]

    submit_response = client.post(f"/api/v1/evidence/{evidence_id}/submit",
                                  headers={"Authorization": f"Bearer {student_token}"})
    assert submit_response.status_code == 200

    review_data = {
        "score": 95.5,
        "qualitative_feedback": "Excellent work with NLP terms!",
        "rubric_evaluation": {"content": 95.5}
    }
    response = client.post(f"/api/v1/evidence/{evidence_id}/review",
                           json=review_data,
                           headers={"Authorization": f"Bearer {instructor_token}"})

    assert response.status_code == 200
    reviewed_evidence = response.json()
    assert reviewed_evidence["status"] == "approved"
    assert reviewed_evidence["score"] == 95.5

def test_instructor_cannot_review_non_submitted_evidence(client: TestClient, instructor_token: str, student_token: str, db_session: Session):
    activity = _create_activity(db_session)
    create_response = client.post("/api/v1/evidence/",
                                json={
                                    "activity_id": str(activity.id),
                                    "content": "Draft evidence.",
                                },
                                headers={"Authorization": f"Bearer {student_token}"})
    assert create_response.status_code == 201
    evidence_id = create_response.json()["id"]

    response = client.post(f"/api/v1/evidence/{evidence_id}/review",
                           json={"score": 80},
                           headers={"Authorization": f"Bearer {instructor_token}"})
    assert response.status_code == 400
    assert "Only submitted evidence can be reviewed" in response.json()["detail"]

def test_student_cannot_review_evidence(client: TestClient, student_token: str, db_session: Session):
    activity = _create_activity(db_session)
    create_response = client.post("/api/v1/evidence/",
                                json={
                                    "activity_id": str(activity.id),
                                    "content": "Student evidence.",
                                },
                                headers={"Authorization": f"Bearer {student_token}"})
    assert create_response.status_code == 201
    evidence_id = create_response.json()["id"]

    submit_response = client.post(f"/api/v1/evidence/{evidence_id}/submit",
                                  headers={"Authorization": f"Bearer {student_token}"})
    assert submit_response.status_code == 200

    response = client.post(f"/api/v1/evidence/{evidence_id}/review",
                           json={"score": 90},
                           headers={"Authorization": f"Bearer {student_token}"})
    assert response.status_code == 403
    assert "Se requiere rol de instructor" in response.json()["detail"]

# --- Test Progress Flow ---
def test_student_can_get_own_progress_dashboard(client: TestClient, student_token: str):
    module_id = uuid4()
    response = client.get(f"/api/v1/progress/dashboard/{module_id}",
                          headers={"Authorization": f"Bearer {student_token}"})
    assert response.status_code == 200
    dashboard_data = response.json()
    assert dashboard_data["user_id"] is not None
    assert dashboard_data["module_title"].startswith("Learning Dashboard for")

def test_student_cannot_access_other_progress_dashboard(client: TestClient, student_token: str, db_session: Session):
    module_id = uuid4()
    response = client.get(f"/api/v1/progress/dashboard/{module_id}",
                          headers={"Authorization": f"Bearer {student_token}"})
    assert response.status_code == 200

def test_progress_dashboard_filters_by_active_theme(client: TestClient, student_token: str, db_session: Session):
    pass

# --- Test My Evidences Endpoint ---
def test_my_evidences_returns_only_students_own_data(client: TestClient, student_token: str, instructor_token: str, db_session: Session):
    activity = _create_activity(db_session)
    client.post("/api/v1/evidence/",
                json={"activity_id": str(activity.id), "content": "Student's evidence."},
                headers={"Authorization": f"Bearer {student_token}"})

    response = client.get("/api/v1/evidence/my", headers={"Authorization": f"Bearer {student_token}"})
    assert response.status_code == 200
    evidences = response.json()
    assert len(evidences) > 0

def test_my_evidences_unauthenticated(client: TestClient, disable_auth):
    response = client.get("/api/v1/evidence/my")
    assert response.status_code == 401

# --- Test Get All Evidences Endpoint (Instructor only) ---
def test_get_all_evidences_by_instructor(client: TestClient, instructor_token: str):
    response = client.get("/api/v1/evidence/", headers={"Authorization": f"Bearer {instructor_token}"})
    assert response.status_code == 200

def test_get_all_evidences_by_student(client: TestClient, student_token: str):
    response = client.get("/api/v1/evidence/", headers={"Authorization": f"Bearer {student_token}"})
    assert response.status_code == 403
    assert "Se requiere rol de instructor" in response.json()["detail"]

# --- Test NLP Placeholder ---
def test_review_evidence_updates_user_progress_with_nlp_context(client: TestClient, instructor_token: str, student_token: str, db_session: Session):
    activity = _create_activity(db_session)
    create_response = client.post("/api/v1/evidence/",
                                json={
                                    "activity_id": str(activity.id),
                                    "content": "This evidence discusses machine learning and NLP.",
                                    "confidence_level": 4,
                                },
                                headers={"Authorization": f"Bearer {student_token}"})
    assert create_response.status_code == 201
    evidence_id = create_response.json()["id"]

    submit_response = client.post(f"/api/v1/evidence/{evidence_id}/submit",
                                  headers={"Authorization": f"Bearer {student_token}"})
    assert submit_response.status_code == 200

    review_response = client.post(f"/api/v1/evidence/{evidence_id}/review",
                                  json={"score": 90, "qualitative_feedback": "Good use of terms."},
                                  headers={"Authorization": f"Bearer {instructor_token}"})
    assert review_response.status_code == 200
    assert review_response.json()["status"] == "approved"
