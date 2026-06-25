from __future__ import annotations

from uuid import uuid4

from app.providers.telephony.base import CallRequest, CallStartResult, TelephonyProvider


class MockTelephonyProvider(TelephonyProvider):
    name = "mock"

    async def place_call(self, request: CallRequest) -> CallStartResult:
        call_id = f"mock-{uuid4().hex[:12]}"
        return CallStartResult(
            provider=self.name,
            provider_call_id=call_id,
            payload={
                "mock": True,
                "phone_number": request.phone_number,
                "script_key": request.script_key,
                "lead_id": request.lead_id,
            },
        )

