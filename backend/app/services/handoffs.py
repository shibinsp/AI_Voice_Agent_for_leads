from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.entities import (
    HandoffEvent,
    HandoffStatus,
    QualificationOutcome,
    QualificationResult,
)
from app.providers.crm.factory import build_crm_provider


def list_handoffs(db: Session, *, limit: int, offset: int) -> tuple[list[HandoffEvent], int]:
    items = db.scalars(
        select(HandoffEvent)
        .order_by(HandoffEvent.created_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    total = db.scalar(select(func.count()).select_from(HandoffEvent)) or 0
    return list(items), total


def create_handoff_for_qualification(
    *,
    db: Session,
    qualification: QualificationResult,
    settings: Settings | None = None,
) -> HandoffEvent:
    settings = settings or get_settings()
    should_send = qualification.outcome in {
        QualificationOutcome.QUALIFIED,
        QualificationOutcome.CALLBACK_REQUESTED,
        QualificationOutcome.NEEDS_REVIEW,
    }
    event = HandoffEvent(
        qualification_result_id=qualification.id,
        lead_id=qualification.lead_id,
        channel=settings.handoff_channel,
        destination=settings.operator_destination,
        status=HandoffStatus.PENDING if should_send else HandoffStatus.SKIPPED,
        payload=_build_payload(qualification),
        response_payload={},
    )
    db.add(event)
    db.flush()

    if not should_send:
        db.commit()
        db.refresh(event)
        return event

    try:
        crm_result = build_crm_provider(settings).sync_qualification(event.payload)
        if settings.handoff_channel == "webhook" and settings.handoff_webhook_url:
            response_payload = _post_webhook(settings.handoff_webhook_url, event.payload)
            event.status = HandoffStatus.SENT
            event.response_payload = {
                "handoff": response_payload,
                "crm": crm_result.provider_payload,
            }
            event.sent_at = datetime.now(timezone.utc)
        else:
            event.status = HandoffStatus.SENT
            event.response_payload = {
                "mock": True,
                "destination": settings.operator_destination,
                "crm": crm_result.provider_payload,
            }
            event.sent_at = datetime.now(timezone.utc)
    except Exception as exc:
        event.status = HandoffStatus.FAILED
        event.failure_reason = str(exc)

    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def _post_webhook(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    with httpx.Client(timeout=10) as client:
        response = client.post(url, json=payload)
    response.raise_for_status()
    try:
        return response.json()
    except ValueError:
        return {"status_code": response.status_code, "text": response.text[:500]}


def _build_payload(qualification: QualificationResult) -> dict[str, Any]:
    lead = qualification.lead
    return {
        "lead_id": qualification.lead_id,
        "lead_name": lead.full_name if lead else None,
        "phone_number": lead.phone_number if lead else None,
        "outcome": qualification.outcome.value,
        "score": qualification.score,
        "summary": qualification.summary,
        "fields": qualification.fields,
    }
