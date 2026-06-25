from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import CallAttempt, CallAttemptStatus, LeadStatus


def apply_exotel_status_callback(db: Session, payload: dict[str, Any]) -> CallAttempt | None:
    provider_call_id = payload.get("CallSid") or payload.get("call_sid")
    if not provider_call_id:
        return None

    attempt = db.scalar(
        select(CallAttempt).where(CallAttempt.provider_call_id == provider_call_id)
    )
    if attempt is None:
        return None

    status_text = str(payload.get("Status", "")).lower().strip()
    attempt.status = _map_exotel_status(status_text)
    attempt.provider_payload = {
        **attempt.provider_payload,
        "status_callback": payload,
    }
    if attempt.status in {
        CallAttemptStatus.COMPLETED,
        CallAttemptStatus.BUSY,
        CallAttemptStatus.NO_ANSWER,
        CallAttemptStatus.FAILED,
    }:
        attempt.completed_at = datetime.now(timezone.utc)

    if attempt.status == CallAttemptStatus.COMPLETED:
        attempt.lead.status = LeadStatus.CONTACTED
    elif attempt.status in {
        CallAttemptStatus.BUSY,
        CallAttemptStatus.NO_ANSWER,
        CallAttemptStatus.FAILED,
    }:
        attempt.lead.status = LeadStatus.FAILED

    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


def _map_exotel_status(status_text: str) -> CallAttemptStatus:
    mapping = {
        "completed": CallAttemptStatus.COMPLETED,
        "busy": CallAttemptStatus.BUSY,
        "no-answer": CallAttemptStatus.NO_ANSWER,
        "failed": CallAttemptStatus.FAILED,
        "in-progress": CallAttemptStatus.IN_PROGRESS,
    }
    return mapping.get(status_text, CallAttemptStatus.FAILED)

