import hashlib
import hmac
import json

from app.core.config import get_settings


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
                            "leadgen_id": "lead-001",
                            "form_id": "form-123",
                            "campaign_id": "campaign-123",
                            "page_id": "page-123",
                            "created_time": 1761234567,
                        },
                    }
                ],
            }
        ],
    }


def test_meta_webhook_verification_success(client):
    response = client.get(
        "/api/v1/webhooks/meta/leadgen",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "test-verify-token",
            "hub.challenge": "challenge-token",
        },
    )
    assert response.status_code == 200
    assert response.text == "challenge-token"


def test_meta_webhook_verification_failure(client):
    response = client.get(
        "/api/v1/webhooks/meta/leadgen",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong-token",
            "hub.challenge": "challenge-token",
        },
    )
    assert response.status_code == 403


def test_meta_webhook_creates_lead_and_call_attempt(client):
    response = client.post("/api/v1/webhooks/meta/leadgen", json=_leadgen_payload())
    assert response.status_code == 200
    payload = response.json()
    assert payload["created"] == 1
    assert payload["duplicates"] == 0
    assert len(payload["scheduled_call_attempt_ids"]) == 1

    leads = client.get("/api/v1/leads")
    assert leads.status_code == 200
    lead_items = leads.json()["items"]
    assert len(lead_items) == 1
    assert lead_items[0]["external_lead_id"] == "lead-001"
    assert lead_items[0]["phone_number"] == "+919876543210"

    attempts = client.get("/api/v1/call-attempts")
    assert attempts.status_code == 200
    attempt_items = attempts.json()["items"]
    assert len(attempt_items) == 1
    assert attempt_items[0]["status"] == "initiated"
    assert attempt_items[0]["provider"] == "mock"


def test_meta_webhook_is_idempotent_for_duplicate_leadgen_id(client):
    first = client.post("/api/v1/webhooks/meta/leadgen", json=_leadgen_payload())
    assert first.status_code == 200

    second = client.post("/api/v1/webhooks/meta/leadgen", json=_leadgen_payload())
    assert second.status_code == 200
    payload = second.json()
    assert payload["created"] == 0
    assert payload["duplicates"] == 1

    leads = client.get("/api/v1/leads")
    attempts = client.get("/api/v1/call-attempts")
    assert leads.json()["total"] == 1
    assert attempts.json()["total"] == 1


def test_meta_webhook_requires_signature_when_app_secret_is_configured(client, monkeypatch):
    monkeypatch.setenv("META_APP_SECRET", "meta-test-secret")
    get_settings.cache_clear()

    response = client.post("/api/v1/webhooks/meta/leadgen", json=_leadgen_payload())

    assert response.status_code == 403


def test_meta_webhook_accepts_valid_signature(client, monkeypatch):
    secret = "meta-test-secret"
    monkeypatch.setenv("META_APP_SECRET", secret)
    get_settings.cache_clear()
    body = json.dumps(_leadgen_payload(), separators=(",", ":")).encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()

    response = client.post(
        "/api/v1/webhooks/meta/leadgen",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": f"sha256={signature}",
        },
    )

    assert response.status_code == 200
    assert response.json()["created"] == 1
