from typing import Any

from app.providers.crm.base import CrmProvider, CrmSyncResult


class MockCrmProvider(CrmProvider):
    name = "mock"

    def sync_qualification(self, payload: dict[str, Any]) -> CrmSyncResult:
        return CrmSyncResult(synced=True, provider_payload={"mock": True, "payload": payload})

