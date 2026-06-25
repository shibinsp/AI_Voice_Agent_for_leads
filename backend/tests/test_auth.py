from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.db.session import get_engine, get_session_factory, init_db
from app.main import app


@pytest.fixture()
def auth_client(
    tmp_path: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[TestClient, None, None]:
    db_path = tmp_path / "auth-test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("ADMIN_USERNAME", "ops")
    monkeypatch.setenv("ADMIN_PASSWORD", "secure-local-password")
    monkeypatch.setenv("AUTH_SECRET_KEY", "test-secret-key-with-enough-entropy")

    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()
    init_db()

    with TestClient(app) as test_client:
        yield test_client

    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()


def test_login_returns_bearer_token(auth_client: TestClient):
    response = auth_client.post(
        "/api/v1/auth/login",
        json={"username": "ops", "password": "secure-local-password"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]
    assert payload["username"] == "ops"
    assert payload["expires_in"] > 0


def test_login_rejects_invalid_password(auth_client: TestClient):
    response = auth_client.post(
        "/api/v1/auth/login",
        json={"username": "ops", "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_protected_routes_require_token(auth_client: TestClient):
    response = auth_client.get("/api/v1/agents")

    assert response.status_code == 401


def test_protected_routes_accept_valid_token(auth_client: TestClient):
    login_response = auth_client.post(
        "/api/v1/auth/login",
        json={"username": "ops", "password": "secure-local-password"},
    )
    token = login_response.json()["access_token"]

    agents_response = auth_client.get(
        "/api/v1/agents",
        headers={"Authorization": f"Bearer {token}"},
    )
    me_response = auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert agents_response.status_code == 200
    assert me_response.status_code == 200
    assert me_response.json() == {"username": "ops"}


def test_production_rejects_unsafe_auth_placeholders(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("ADMIN_PASSWORD", "replace-with-a-long-random-password")
    monkeypatch.setenv("AUTH_SECRET_KEY", "replace-with-at-least-32-random-bytes")
    monkeypatch.setenv("META_VERIFY_TOKEN", "replace-with-meta-verify-token")
    monkeypatch.setenv("ALLOW_MOCK_META_LEADS", "false")
    monkeypatch.setenv("TELEPHONY_PROVIDER", "exotel")

    get_settings.cache_clear()

    with pytest.raises(ValueError, match="Production configuration is not secure"):
        get_settings()

    get_settings.cache_clear()
