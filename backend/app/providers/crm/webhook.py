from typing import Any

import httpx

from app.core.config import Settings
from app.providers.crm.base import CrmProvider, CrmSyncResult


class WebhookCrmProvider(CrmProvider):
    name = "webhook"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def sync_qualification(self, payload: dict[str, Any]) -> CrmSyncResult:
        if not self.settings.crm_webhook_url:
            raise RuntimeError("CRM_WEBHOOK_URL is required")
        with httpx.Client(timeout=10) as client:
            response = client.post(self.settings.crm_webhook_url, json=payload)
        response.raise_for_status()
        try:
            response_payload = response.json()
        except ValueError:
            response_payload = {"status_code": response.status_code, "text": response.text[:500]}
        return CrmSyncResult(synced=True, provider_payload=response_payload)

