from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import Settings


@dataclass(slots=True)
class MetaLeadDetails:
    full_name: str | None
    phone_number: str | None
    email: str | None
    city: str | None
    preferred_language: str | None
    raw_fields: dict[str, Any]


class MetaLeadClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def fetch_lead(self, leadgen_id: str) -> MetaLeadDetails:
        if not self.settings.meta_access_token:
            if self.settings.environment != "production" and self.settings.allow_mock_meta_leads:
                return _build_mock_lead_details(leadgen_id)
            raise RuntimeError(
                "META_ACCESS_TOKEN is not configured. Set live credentials or enable mock leads outside production."
            )

        url = f"https://graph.facebook.com/{self.settings.meta_api_version}/{leadgen_id}"
        params = {
            "access_token": self.settings.meta_access_token,
            "fields": "created_time,field_data",
        }
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url, params=params)
        response.raise_for_status()
        return _parse_meta_lead_payload(response.json())


def _parse_meta_lead_payload(payload: dict[str, Any]) -> MetaLeadDetails:
    field_map: dict[str, Any] = {}
    for item in payload.get("field_data", []):
        name = item.get("name")
        values = item.get("values") or []
        if not name or not values:
            continue
        field_map[name] = values[0]

    return MetaLeadDetails(
        full_name=field_map.get("full_name") or field_map.get("name"),
        phone_number=field_map.get("phone_number"),
        email=field_map.get("email"),
        city=field_map.get("city"),
        preferred_language=field_map.get("preferred_language"),
        raw_fields=field_map,
    )


def _build_mock_lead_details(leadgen_id: str) -> MetaLeadDetails:
    suffix = "".join(ch for ch in leadgen_id if ch.isdigit())[-4:] or "2401"
    return MetaLeadDetails(
        full_name=f"Demo Lead {suffix}",
        phone_number=f"98{suffix}43210"[-10:],
        email=f"lead{suffix}@demo.local",
        city="Hyderabad",
        preferred_language="te-IN",
        raw_fields={
            "full_name": f"Demo Lead {suffix}",
            "phone_number": f"98{suffix}43210"[-10:],
            "email": f"lead{suffix}@demo.local",
            "city": "Hyderabad",
            "preferred_language": "te-IN",
            "mock_source": "local-dev",
        },
    )
