from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.entities import CallAttemptStatus


class CallAttemptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_id: int
    provider: str
    script_key: str
    phone_number: str
    provider_call_id: str | None
    status: CallAttemptStatus
    failure_reason: str | None
    provider_payload: dict
    requested_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class CallAttemptListResponse(BaseModel):
    items: list[CallAttemptRead]
    total: int

