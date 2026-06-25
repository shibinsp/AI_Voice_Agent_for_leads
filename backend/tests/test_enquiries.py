from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.session import get_engine, get_session_factory, init_db
from app.main import app


def _enquiry_payload() -> dict:
    return {
        "full_name": "Sita Rao",
        "phone_number": "9876543210",
        "requirement": "2BHK flat near Gachibowli, budget around 80 lakhs",
        "source": "linkedin",
    }


def test_enquiry_creates_lead_and_runs_web_call(client):
    response = client.post("/api/v1/enquiries", json=_enquiry_payload())
    assert response.status_code == 201
    body = response.json()
    session_id = body["session_id"]
    assert body["lead_id"] and session_id and body["token"]
    assert body["opening_line"]

    # the enquiry shows up as a lead carrying its requirement
    leads = client.get("/api/v1/leads").json()["items"]
    lead = next(l for l in leads if l["id"] == body["lead_id"])
    assert lead["raw_fields"]["requirement"].startswith("2BHK flat near Gachibowli")
    assert lead["raw_fields"]["source"] == "linkedin"
    assert lead["raw_fields"]["channel"] == "enquiry_link"

    # drive the browser web call over the WebSocket with the session-scoped token
    with client.websocket_connect(
        f"/api/v1/voice-sessions/{session_id}/stream?token={body['token']}"
    ) as ws:
        assert ws.receive_json()["type"] == "ready"
        ws.send_json({"type": "text", "text": "Avunu, naaku appointment kavali, interested", "confidence": 0.95})
        turn = ws.receive_json()
        assert turn["type"] == "turn"
        assert turn["agent_text"]
        ws.send_json({"type": "end"})
        completed = ws.receive_json()
        assert completed["type"] == "completed"

    # a genuine enquiry is routed to the client as a handoff
    handoffs = client.get("/api/v1/handoffs").json()
    assert handoffs["total"] >= 1


@pytest.fixture()
def auth_client(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> Generator[TestClient, None, None]:
    db_path = tmp_path / "auth.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "admin123")
    monkeypatch.setenv("AUTH_SECRET_KEY", "test-secret-key-please-change")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("TELEPHONY_PROVIDER", "mock")

    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()
    init_db()
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()


def test_enquiry_token_is_scoped_to_its_session(auth_client):
    a = auth_client.post("/api/v1/enquiries", json=_enquiry_payload()).json()
    b = auth_client.post("/api/v1/enquiries", json=_enquiry_payload()).json()
    assert a["session_id"] != b["session_id"]

    # token A opens session A
    with auth_client.websocket_connect(
        f"/api/v1/voice-sessions/{a['session_id']}/stream?token={a['token']}"
    ) as ws:
        assert ws.receive_json()["type"] == "ready"

    # token A must NOT open session B
    with pytest.raises(Exception):
        with auth_client.websocket_connect(
            f"/api/v1/voice-sessions/{b['session_id']}/stream?token={a['token']}"
        ) as ws:
            ws.receive_json()

    # operator routes still require a bearer token
    assert auth_client.get("/api/v1/leads").status_code == 401
