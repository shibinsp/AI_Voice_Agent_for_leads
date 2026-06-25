from __future__ import annotations

from typing import Any

import httpx

from app.core.config import Settings
from app.providers.telephony.base import CallRequest, CallStartResult, TelephonyProvider


class ExotelProvider(TelephonyProvider):
    name = "exotel"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def _base_url(self) -> str:
        host = "api.in.exotel.com" if self.settings.exotel_region == "in" else "api.exotel.com"
        return f"https://{host}/v1/Accounts/{self.settings.exotel_account_sid}/Calls/connect"

    def _auth(self) -> tuple[str, str]:
        if not self.settings.exotel_api_key or not self.settings.exotel_api_token:
            raise RuntimeError("Exotel credentials are missing")
        return self.settings.exotel_api_key, self.settings.exotel_api_token

    def _build_payload(self, request: CallRequest) -> dict[str, str]:
        if not self.settings.exotel_caller_id:
            raise RuntimeError("EXOTEL_CALLER_ID is required")
        if not self.settings.exotel_from_number:
            raise RuntimeError("EXOTEL_FROM_NUMBER is required")

        payload: dict[str, str] = {
            "From": self.settings.exotel_from_number,
            "To": request.phone_number,
            "CallerId": self.settings.exotel_caller_id,
            "CallType": "trans",
            "CustomField": f"lead:{request.lead_id}",
        }
        if self.settings.exotel_status_callback_url:
            payload["StatusCallback"] = self.settings.exotel_status_callback_url
            payload["StatusCallbackContentType"] = "application/json"
            payload["StatusCallbackEvents"] = "terminal"
        if self.settings.exotel_stream_url:
            payload["StreamUrl"] = self.settings.exotel_stream_url
            payload["StreamBegin"] = "at Leg2Connect"
        if self.settings.exotel_flow_url:
            payload["Url"] = self.settings.exotel_flow_url
        return payload

    async def place_call(self, request: CallRequest) -> CallStartResult:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                self._base_url,
                data=self._build_payload(request),
                auth=self._auth(),
            )
        response.raise_for_status()
        payload = response.json()
        provider_call_id = _extract_call_id(payload)
        if not provider_call_id:
            raise RuntimeError("Exotel response did not include a call identifier")
        return CallStartResult(
            provider=self.name,
            provider_call_id=provider_call_id,
            payload=payload,
        )


def _extract_call_id(payload: dict[str, Any]) -> str | None:
    call = payload.get("Call") if isinstance(payload, dict) else None
    if isinstance(call, dict):
        return call.get("Sid") or call.get("CallSid")
    return payload.get("CallSid") if isinstance(payload, dict) else None

