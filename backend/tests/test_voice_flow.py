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
                            "leadgen_id": "lead-voice-001",
                            "form_id": "form-voice-001",
                            "campaign_id": "campaign-voice-001",
                            "page_id": "page-123",
                            "created_time": 1761234567,
                        },
                    }
                ],
            }
        ],
    }


def test_demo_voice_session_qualifies_and_creates_handoff(client):
    agent_response = client.post("/api/v1/agents", json=_agent_payload())
    assert agent_response.status_code == 201

    webhook_response = client.post("/api/v1/webhooks/meta/leadgen", json=_leadgen_payload())
    assert webhook_response.status_code == 200

    attempts_response = client.get("/api/v1/call-attempts")
    assert attempts_response.status_code == 200
    attempt = attempts_response.json()["items"][0]

    session_response = client.post(f"/api/v1/voice-sessions/from-call-attempt/{attempt['id']}/demo")
    assert session_response.status_code == 200
    session = session_response.json()
    assert session["status"] == "completed"
    assert len(session["transcript_turns"]) >= 3
    assert session["qualification_result"]["outcome"] in {
        "qualified",
        "callback_requested",
        "needs_review",
    }

    handoffs_response = client.get("/api/v1/handoffs")
    assert handoffs_response.status_code == 200
    handoffs = handoffs_response.json()
    assert handoffs["total"] == 1
    assert handoffs["items"][0]["status"] == "sent"


def test_integration_readiness_reports_mock_ready(client):
    response = client.get("/api/v1/integrations/readiness")
    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"] is True
    assert payload["telephony"] is True
    assert payload["sarvam"] is True
    assert payload["llm"] is True
    assert payload["crm"] is True
    assert payload["handoff"] is True
    assert payload["missing"] == []
