from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_session_factory
from app.models.entities import CallAttempt, CallAttemptStatus, LeadStatus
from app.providers.telephony.base import CallRequest, TelephonyProvider
from app.providers.telephony.factory import build_telephony_provider


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def dispatch_call_attempt(
    *,
    db: Session,
    attempt_id: int,
    telephony_provider: TelephonyProvider,
) -> CallAttempt:
    attempt = db.get(CallAttempt, attempt_id)
    if attempt is None:
        raise ValueError(f"Call attempt {attempt_id} not found")
    if attempt.status not in {CallAttemptStatus.QUEUED, CallAttemptStatus.FAILED}:
        return attempt

    request = CallRequest(
        phone_number=attempt.phone_number,
        caller_id=None,
        from_number=None,
        script_key=attempt.script_key,
        language=attempt.lead.preferred_language,
        lead_id=attempt.lead_id,
        lead_context={
            "lead_id": attempt.lead_id,
            "name": attempt.lead.full_name,
            "phone_number": attempt.phone_number,
            "campaign_id": attempt.lead.campaign_id,
        },
    )

    try:
        result = await telephony_provider.place_call(request)
        attempt.provider = result.provider
        attempt.provider_call_id = result.provider_call_id
        attempt.provider_payload = result.payload
        attempt.status = CallAttemptStatus.INITIATED
        attempt.started_at = _now()
        attempt.failure_reason = None
        attempt.lead.status = LeadStatus.CALLING
    except Exception as exc:
        attempt.status = CallAttemptStatus.FAILED
        attempt.failure_reason = str(exc)
        attempt.provider = telephony_provider.name
        attempt.lead.status = LeadStatus.FAILED

    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


async def dispatch_call_attempt_in_background(attempt_id: int) -> None:
    session_factory = get_session_factory()
    db = session_factory()
    try:
        provider = build_telephony_provider(get_settings())
        await dispatch_call_attempt(
            db=db,
            attempt_id=attempt_id,
            telephony_provider=provider,
        )
    finally:
        db.close()

