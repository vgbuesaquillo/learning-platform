import os
import sys
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.domain.models import Base, User
from app.main import app
from app.core.dependencies import get_current_user, require_instructor

TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

from app.infrastructure.database import get_db as original_get_db

def override_get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[original_get_db] = override_get_db

_STUDENT_UUID = UUID("00000000-0000-0000-0000-000000000001")
_INSTRUCTOR_UUID = UUID("00000000-0000-0000-0000-000000000002")

@pytest.fixture(scope="session", autouse=True)
def setup_users():
    db = SessionLocal()
    existing = db.query(User).filter(User.email == "student@test.com").first()
    if not existing:
        db.add(User(id=_STUDENT_UUID, email="student@test.com", full_name="Test Student", hashed_password="x", is_instructor=False))
        db.add(User(id=_INSTRUCTOR_UUID, email="instructor@test.com", full_name="Test Instructor", hashed_password="x", is_instructor=True))
        db.commit()
    db.close()

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def _make_mock_user(uid, email, name, is_instructor):
    return type("MockUser", (), {
        "id": uid,
        "email": email,
        "full_name": name,
        "is_instructor": is_instructor,
        "is_active": True,
    })()

@pytest.fixture(autouse=True)
def _override_auth():
    student = _make_mock_user(_STUDENT_UUID, "student@test.com", "Test Student", False)
    app.dependency_overrides[get_current_user] = lambda: student
    yield
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(require_instructor, None)

@pytest.fixture
def student_token():
    return "valid-student-token"

@pytest.fixture
def instructor_token():
    instructor = _make_mock_user(_INSTRUCTOR_UUID, "instructor@test.com", "Test Instructor", True)
    app.dependency_overrides[get_current_user] = lambda: instructor
    app.dependency_overrides[require_instructor] = lambda: instructor
    return "valid-instructor-token"
