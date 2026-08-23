import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Set before importing anything that builds the engine at module scope.
TEST_DB_PATH = Path(__file__).resolve().parent / "test_app.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"

from app.core.rate_limit import REQUEST_LOG  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.services.users import create_user  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def remove_test_database_file() -> Iterator[None]:
    """Keep the scratch SQLite file from being left behind in the source tree."""
    yield
    TEST_DB_PATH.unlink(missing_ok=True)


@pytest.fixture(autouse=True)
def reset_database() -> None:
    REQUEST_LOG.clear()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def authenticated_client(client: TestClient) -> tuple[TestClient, str]:
    session = SessionLocal()
    try:
        create_user(session, email="sam@example.com", password="secret", is_admin=True)
    finally:
        session.close()
    login_response = client.post(
        "/api/auth/login",
        json={"email": "sam@example.com", "password": "secret"},
    )
    assert login_response.status_code == 200
    csrf_token = login_response.cookies.get("fridgestare_csrf")
    assert csrf_token
    return client, csrf_token
