from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.entities import LeadStatus


class LeadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int | None
    campaign_id: int | None
    external_lead_id: str
    external_page_id: str | None
    full_name: str | None
    phone_number: str | None
    email: str | None
    preferred_language: str
    city: str | None
    raw_fields: dict
    status: LeadStatus
    created_at: datetime
    updated_at: datetime


class LeadListResponse(BaseModel):
    items: list[LeadRead]
    total: int

