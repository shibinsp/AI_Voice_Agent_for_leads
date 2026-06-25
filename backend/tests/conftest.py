from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api.deps import get_meta_lead_client
from app.core.config import get_settings
from app.db.session import get_engine, get_session_factory, init_db
from app.main import app
from app.services.meta import MetaLeadDetails


class StubMetaLeadClient:
    async def fetch_lead(self, leadgen_id: str) -> MetaLeadDetails:
        return MetaLeadDetails(
            full_name="Ravi Teja",
            phone_number="9876543210",
            email="ravi@example.com",
            city="Hyderabad",
            preferred_language="te-IN",
            raw_fields={
                "full_name": "Ravi Teja",
                "phone_number": "9876543210",
                "email": "ravi@example.com",
                "city": "Hyderabad",
            },
        )


@pytest.fixture()
def client(tmp_path: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("META_VERIFY_TOKEN", "test-verify-token")
    monkeypatch.setenv("TELEPHONY_PROVIDER", "mock")
    monkeypatch.setenv("AUTO_DISPATCH_CALLS", "true")
    monkeypatch.setenv("AUTH_ENABLED", "false")
    # Pin providers to mock so a live backend/.env can't leak into tests (determinism + no network).
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("SARVAM_API_KEY", "")
    monkeypatch.setenv("CRM_PROVIDER", "mock")
    monkeypatch.setenv("HANDOFF_CHANNEL", "mock")

    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()
    init_db()

    app.dependency_overrides[get_meta_lead_client] = lambda: StubMetaLeadClient()
    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()
