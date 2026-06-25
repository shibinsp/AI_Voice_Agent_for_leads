from pydantic import BaseModel


class MetaLeadgenValue(BaseModel):
    ad_id: str | None = None
    adgroup_id: str | None = None
    campaign_id: str | None = None
    created_time: int | None = None
    form_id: str | None = None
    leadgen_id: str | None = None
    page_id: str | None = None


class MetaWebhookChange(BaseModel):
    field: str
    value: MetaLeadgenValue


class MetaWebhookEntry(BaseModel):
    id: str
    time: int
    changes: list[MetaWebhookChange]


class MetaWebhookEvent(BaseModel):
    object: str
    entry: list[MetaWebhookEntry]


class MetaWebhookResponse(BaseModel):
    received: int
    created: int
    duplicates: int
    scheduled_call_attempt_ids: list[int]

