def test_agents_list_starts_empty(client):
    response = client.get("/api/v1/agents")
    assert response.status_code == 200
    payload = response.json()
    assert payload["items"] == []
    assert payload["total"] == 0


def test_create_agent(client):
    payload = {
        "name": "Hyderabad Clinic Qualifier",
        "script_key": "clinic_v1",
        "vertical": "clinics",
        "language": "te-IN",
        "voice_provider": "sarvam",
        "telephony_provider": "mock",
        "description": "First-touch callback agent for clinic leads.",
        "opening_line": "Namaskaram, this is a quick callback regarding your appointment inquiry.",
        "qualification_goal": "Capture specialization, urgency, and preferred callback window.",
        "is_active": True,
    }
    response = client.post("/api/v1/agents", json=payload)
    assert response.status_code == 201
    created = response.json()
    assert created["name"] == payload["name"]
    assert created["script_key"] == payload["script_key"]
    assert created["vertical"] == payload["vertical"]

    list_response = client.get("/api/v1/agents")
    assert list_response.status_code == 200
    listed = list_response.json()
    assert listed["total"] == 1
    assert listed["items"][0]["script_key"] == "clinic_v1"


def test_create_agent_rejects_duplicate_script_key(client):
    payload = {
        "name": "Agent One",
        "script_key": "shared_key",
        "vertical": "real_estate",
        "language": "te-IN",
        "voice_provider": "sarvam",
        "telephony_provider": "mock",
        "description": None,
        "opening_line": None,
        "qualification_goal": None,
        "is_active": True,
    }
    first = client.post("/api/v1/agents", json=payload)
    assert first.status_code == 201

    second_payload = {
        **payload,
        "name": "Agent Two",
    }
    second = client.post("/api/v1/agents", json=second_payload)
    assert second.status_code == 409
    assert second.json()["detail"] == "Agent script_key already exists"


def test_update_agent_status(client):
    create_payload = {
        "name": "Insurance Callback Agent",
        "script_key": "insurance_v1",
        "vertical": "insurance",
        "language": "te-IN",
        "voice_provider": "sarvam",
        "telephony_provider": "mock",
        "description": "Validates lead intent and budget range.",
        "opening_line": "Namaskaram, I am calling about your policy request.",
        "qualification_goal": "Collect policy type and time horizon.",
        "is_active": True,
    }
    created = client.post("/api/v1/agents", json=create_payload).json()

    update_response = client.patch(
        f"/api/v1/agents/{created['id']}",
        json={
            "is_active": False,
            "description": "Paused while the script is being refined.",
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["is_active"] is False
    assert updated["description"] == "Paused while the script is being refined."


def test_new_campaign_uses_active_agent_script(client):
    agent_payload = {
        "name": "Real Estate Site Visit Agent",
        "script_key": "real_estate_site_visit_v1",
        "vertical": "real_estate",
        "language": "te-IN",
        "voice_provider": "sarvam",
        "telephony_provider": "mock",
        "description": "Qualifies site visit intent.",
        "opening_line": "Namaskaram, I am calling about your property inquiry.",
        "qualification_goal": "Capture location, budget, and visit timing.",
        "is_active": True,
    }
    agent_response = client.post("/api/v1/agents", json=agent_payload)
    assert agent_response.status_code == 201

    webhook_payload = {
        "object": "page",
        "entry": [
            {
                "id": "page-123",
                "time": 1761234567,
                "changes": [
                    {
                        "field": "leadgen",
                        "value": {
                            "leadgen_id": "lead-agent-script-001",
                            "form_id": "form-agent-script-001",
                            "campaign_id": "campaign-agent-script-001",
                            "page_id": "page-123",
                            "created_time": 1761234567,
                        },
                    }
                ],
            }
        ],
    }
    webhook_response = client.post("/api/v1/webhooks/meta/leadgen", json=webhook_payload)
    assert webhook_response.status_code == 200

    attempts = client.get("/api/v1/call-attempts").json()["items"]
    assert attempts[0]["script_key"] == "real_estate_site_visit_v1"
