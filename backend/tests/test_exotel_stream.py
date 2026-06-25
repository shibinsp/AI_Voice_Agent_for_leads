from __future__ import annotations

import asyncio
import struct
from base64 import b64encode
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.session import get_engine, get_session_factory, init_db
from app.main import app
from app.services.exotel_stream import ExotelCallBridge


def _agent_payload() -> dict:
    return {
        "name": "RealEstate Telugu",
        "script_key": "re_v1",
        "vertical": "real_estate",
        "language": "te-IN",
        "voice_provider": "sarvam",
        "telephony_provider": "exotel",
        "description": "x",
        "opening_line": "Namaskaram, meeru submit chesina inquiry gurinchi.",
        "qualification_goal": "Capture area and budget.",
        "is_active": True,
    }


def _leadgen_payload() -> dict:
    return {
        "object": "page",
        "entry": [
            {
                "id": "p1",
                "time": 1,
                "changes": [
                    {
                        "field": "leadgen",
                        "value": {
                            "leadgen_id": "phone-lead-001",
                            "form_id": "f1",
                            "campaign_id": "c1",
                            "page_id": "p1",
                            "created_time": 1,
                        },
                    }
                ],
            }
        ],
    }


def _media(payload_bytes: bytes) -> dict:
    return {"event": "media", "media": {"payload": b64encode(payload_bytes).decode("ascii")}}


def test_exotel_bridge_drives_full_call(client):
    assert client.post("/api/v1/agents", json=_agent_payload()).status_code == 201
    assert client.post("/api/v1/webhooks/meta/leadgen", json=_leadgen_payload()).status_code == 200
    lead_id = client.get("/api/v1/call-attempts").json()["items"][0]["lead_id"]

    sent: list[dict] = []

    async def send(frame: dict) -> None:
        sent.append(frame)

    db = get_session_factory()()
    bridge = ExotelCallBridge(db, get_settings(), send)

    speech = struct.pack("<h", 6000) * 160  # 20 ms of loud tone
    quiet = b"\x00\x00" * 160  # 20 ms of silence

    async def scenario() -> None:
        await bridge.on_start(
            {"event": "start", "stream_sid": "s1", "start": {"custom_field": f"lead:{lead_id}"}}
        )
        for _ in range(15):  # ~300 ms of speech
            await bridge.on_media(_media(speech))
        for _ in range(45):  # trailing silence triggers end-of-utterance
            await bridge.on_media(_media(quiet))
        await bridge.on_stop()

    asyncio.run(scenario())
    db.close()

    # agent audio was streamed back to Exotel as media frames
    assert any(f.get("event") == "media" for f in sent)

    # the call produced a completed voice session with transcript turns + a handoff
    session = client.get("/api/v1/voice-sessions").json()["items"][0]
    assert session["status"] == "completed"
    assert len(session["transcript_turns"]) >= 3  # opening + lead utterance + agent reply
    speakers = {t["speaker"] for t in session["transcript_turns"]}
    assert {"agent", "lead"} <= speakers
    assert client.get("/api/v1/handoffs").json()["total"] >= 1


@pytest.fixture()
def secret_client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'phone.db'}")
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("AUTH_SECRET_KEY", "test-secret-key-please-change")
    monkeypatch.setenv("EXOTEL_STREAM_SECRET", "topsecret")
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


def test_exotel_stream_rejects_bad_token(secret_client):
    with pytest.raises(Exception):
        with secret_client.websocket_connect(
            "/api/v1/telephony/exotel/stream?token=wrong"
        ) as ws:
            ws.receive_json()
