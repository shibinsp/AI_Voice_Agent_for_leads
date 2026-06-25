def _agent_payload() -> dict:
    return {
        "name": "Hyderabad Clinic Qualifier",
        "script_key": "clinic_telugu_v1",
        "vertical": "clinics",
        "language": "te-IN",
        "voice_provider": "sarvam",
        "telephony_provider": "mock",
        "description": "First response agent for clinic appointment leads.",
        "opening_line": "Namaskaram, I am calling about the appointment request you submitted.",
        "qualification_goal": "Capture specialty, urgency, and preferred callback window.",
        "is_active": True,
    }


def _leadgen_payload() -> dict:
    return {
        "object": "page",
        "entry": [
            {
                "id": "page-123",
                "time": 1761234567,
                "changes": [
                    {
                        "field": "leadgen",
                        "value": {
                            "leadgen_id": "lead-stream-001",
                            "form_id": "form-stream-001",
                            "campaign_id": "campaign-stream-001",
                            "page_id": "page-123",
                            "created_time": 1761234567,
                        },
                    }
                ],
            }
        ],
    }


def test_live_stream_loop_produces_turn_and_qualifies(client):
    assert client.post("/api/v1/agents", json=_agent_payload()).status_code == 201
    assert client.post("/api/v1/webhooks/meta/leadgen", json=_leadgen_payload()).status_code == 200

    attempt = client.get("/api/v1/call-attempts").json()["items"][0]

    # Start an in-progress session (HTTP), then drive the loop over the WebSocket.
    session = client.post(f"/api/v1/voice-sessions/from-call-attempt/{attempt['id']}").json()
    session_id = session["id"]
    assert session["status"] == "in_progress"

    with client.websocket_connect(f"/api/v1/voice-sessions/{session_id}/stream") as ws:
        ready = ws.receive_json()
        assert ready["type"] == "ready"
        assert ready["session_id"] == session_id

        ws.send_json({"type": "audio", "audio_base64": "AAAA", "mime_type": "audio/wav"})
        turn = ws.receive_json()
        assert turn["type"] == "turn"
        assert turn["lead_text"]  # mock STT returns a canned Telugu utterance
        assert turn["agent_text"]
        assert turn["agent_audio_base64"]
        assert turn["mime_type"].startswith("audio/")

        ws.send_json({"type": "end"})
        completed = ws.receive_json()
        assert completed["type"] == "completed"
        assert completed["qualification"] is not None
        assert completed["qualification"]["outcome"] in {
            "qualified",
            "callback_requested",
            "needs_review",
            "not_qualified",
        }

    # Session is finalized and a handoff was created.
    final = client.get(f"/api/v1/voice-sessions/{session_id}").json()
    assert final["status"] == "completed"
    assert final["qualification_result"] is not None
    # opening agent turn + lead turn + agent reply = 3 turns minimum
    assert len(final["transcript_turns"]) >= 3

    handoffs = client.get("/api/v1/handoffs").json()
    assert handoffs["total"] >= 1


def test_live_stream_text_path(client):
    """Browser Web Speech API sends already-transcribed text instead of audio."""
    assert client.post("/api/v1/agents", json=_agent_payload()).status_code == 201
    assert client.post("/api/v1/webhooks/meta/leadgen", json=_leadgen_payload()).status_code == 200
    attempt = client.get("/api/v1/call-attempts").json()["items"][0]
    session = client.post(f"/api/v1/voice-sessions/from-call-attempt/{attempt['id']}").json()

    with client.websocket_connect(f"/api/v1/voice-sessions/{session['id']}/stream") as ws:
        assert ws.receive_json()["type"] == "ready"
        ws.send_json({"type": "text", "text": "Naaku appointment kavali repu", "confidence": 0.95})
        turn = ws.receive_json()
        assert turn["type"] == "turn"
        assert turn["lead_text"] == "Naaku appointment kavali repu"
        assert turn["agent_text"]
        # text path carries no synthesized audio
        assert "agent_audio_base64" not in turn
        ws.send_json({"type": "end"})
        assert ws.receive_json()["type"] == "completed"


def test_stream_rejects_unknown_message(client):
    assert client.post("/api/v1/agents", json=_agent_payload()).status_code == 201
    assert client.post("/api/v1/webhooks/meta/leadgen", json=_leadgen_payload()).status_code == 200
    attempt = client.get("/api/v1/call-attempts").json()["items"][0]
    session = client.post(f"/api/v1/voice-sessions/from-call-attempt/{attempt['id']}").json()

    with client.websocket_connect(f"/api/v1/voice-sessions/{session['id']}/stream") as ws:
        assert ws.receive_json()["type"] == "ready"
        ws.send_json({"type": "nonsense"})
        reply = ws.receive_json()
        assert reply["type"] == "error"
