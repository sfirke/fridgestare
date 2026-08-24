import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Set before importing anything that builds the engine at module scope.
TEST_DB_PATH = Path(__file__).resolve().parent / "test_app.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
# Settings still reads the repo-root .env, so pin what the suite depends on rather than
# inheriting a developer's local file. A production-shaped .env sets COOKIE_SECURE=true,
# and the TestClient speaks http, so the CSRF cookie is never stored and every mutating
# request fails with a 403 that has nothing to do with the code under test.
os.environ["APP_ENV"] = "development"
os.environ["COOKIE_SECURE"] = "false"
os.environ["APP_BASE_URL"] = "http://localhost:5173"

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
