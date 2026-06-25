from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Agent, Campaign, CallAttempt, CallAttemptStatus, Lead, LeadStatus
from app.schemas.meta import MetaLeadgenValue
from app.services.meta import MetaLeadClient, MetaLeadDetails


@dataclass(slots=True)
class LeadIngestResult:
    created: bool
    lead_id: int
    call_attempt_id: int | None


async def ingest_meta_lead_event(
    *,
    db: Session,
    change_value: MetaLeadgenValue,
    meta_client: MetaLeadClient,
    default_language: str,
    raw_event: dict[str, Any],
) -> LeadIngestResult:
    existing = db.scalar(
        select(Lead).where(Lead.external_lead_id == change_value.leadgen_id)
    )
    if existing is not None:
        return LeadIngestResult(created=False, lead_id=existing.id, call_attempt_id=None)

    if not change_value.leadgen_id:
        raise ValueError("leadgen_id is required")

    details = await meta_client.fetch_lead(change_value.leadgen_id)
    campaign = _get_or_create_campaign(db, change_value, default_language)

    lead = Lead(
        campaign=campaign,
        external_lead_id=change_value.leadgen_id,
        external_page_id=change_value.page_id,
        full_name=details.full_name,
        phone_number=_normalize_phone(details.phone_number),
        email=details.email,
        preferred_language=details.preferred_language or default_language,
        city=details.city,
        raw_fields=details.raw_fields,
        raw_event=raw_event,
        status=LeadStatus.CALL_QUEUED,
    )
    db.add(lead)
    db.flush()

    attempt = CallAttempt(
        lead_id=lead.id,
        provider="pending",
        script_key=campaign.script_key if campaign else "default_v1",
        phone_number=lead.phone_number or "unknown",
        status=CallAttemptStatus.QUEUED,
        provider_payload={},
    )
    db.add(attempt)
    db.commit()
    db.refresh(lead)
    db.refresh(attempt)
    return LeadIngestResult(created=True, lead_id=lead.id, call_attempt_id=attempt.id)


def _get_or_create_campaign(
    db: Session,
    change_value: MetaLeadgenValue,
    default_language: str,
) -> Campaign:
    if change_value.form_id:
        campaign = db.scalar(
            select(Campaign).where(Campaign.external_form_id == change_value.form_id)
        )
        if campaign is not None:
            return campaign
    default_agent = db.scalar(
        select(Agent).where(Agent.is_active.is_(True)).order_by(Agent.updated_at.desc())
    )
    campaign = Campaign(
        external_form_id=change_value.form_id,
        external_campaign_id=change_value.campaign_id,
        name=f"Meta form {change_value.form_id or 'unknown'}",
        script_key=default_agent.script_key if default_agent else "default_v1",
        language=default_agent.language if default_agent else default_language,
    )
    db.add(campaign)
    db.flush()
    return campaign


def _normalize_phone(phone_number: str | None) -> str | None:
    if phone_number is None:
        return None
    digits = "".join(ch for ch in phone_number if ch.isdigit())
    if len(digits) == 10:
        return f"+91{digits}"
    if len(digits) == 12 and digits.startswith("91"):
        return f"+{digits}"
    if phone_number.startswith("+"):
        return phone_number
    return phone_number
