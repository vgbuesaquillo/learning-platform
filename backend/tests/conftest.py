import sys
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.domain.models import Base
from app.main import app

# --- Path Adjustment for Imports ---
# Add the 'backend' directory to sys.path so that 'app' package can be imported.
# This assumes conftest.py is in `backend/tests/` and pytest is run from the project root.
try:
    import os
    import sys
    # Get the project root directory (where .git is located)
    PROJECT_ROOT = os.getcwd()
    BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
    if BACKEND_DIR not in sys.path:
        sys.path.insert(0, BACKEND_DIR)
except Exception as e:
    print(f"Warning: Failed to adjust sys.path for backend imports: {e}")
# --- End Path Adjustment ---

# In-memory SQLite DB for tests
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables for tests
Base.metadata.create_all(bind=engine)

# Dependency override to use test DB
try:
    # Import the original get_db to override it
    from app.infrastructure.database import get_db as original_get_db
    def override_get_db():
        try:
            db = SessionLocal()
            yield db
        finally:
            db.close()
    app.dependency_overrides[original_get_db] = override_get_db
except ImportError:
    print("Warning: Could not import original get_db. Dependency override might not work.")
except Exception as e:
    print(f"Warning: Could not override get_db dependency: {e}")

# Simple fixtures
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

# Token fixtures would be created using the API or direct DB manipulation in tests
# These are placeholders and might need refinement based on actual token generation logic
@pytest.fixture
def student_token(client: TestClient):
    # In a real scenario, this would involve registering a user and logging in to get a token.
    # For now, returning a dummy token. If token generation requires specific user setup,
    # this fixture would need to be more complex.
    # Example: If registration and login are tested and validated, return a token from there.
    # For now, assume a valid token format.
    return "DUMMY_STUDENT_TOKEN_12345"

@pytest.fixture
def instructor_token(client: TestClient):
    # Similar to student_token, a dummy token for instructor.
    return "DUMMY_INSTRUCTOR_TOKEN_67890"
