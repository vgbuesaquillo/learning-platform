import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend/app is on PYTHONPATH before imports
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.domain.models import Base
from app.main import app

# In-memory SQLite DB setup for tests
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables for tests
Base.metadata.create_all(bind=engine)

# Dependency override to use test DB
try:
    from app.infrastructure.database import get_db as original_get_db

    def override_get_db():
        try:
            db = SessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[original_get_db] = override_get_db
except Exception as e:
    print(f"Warning: Could not override get_db dependency: {e}")


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

# Simple token fixtures (placeholders for tests)
@pytest.fixture
def student_token(client: TestClient):
    return "DUMMY_STUDENT_TOKEN_12345"

@pytest.fixture
def instructor_token(client: TestClient):
    return "DUMMY_INSTRUCTOR_TOKEN_67890"
