from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_app_settings, get_db, get_telephony_provider
from app.core.config import Settings
from app.models.entities import CallAttempt
from app.providers.telephony.base import TelephonyProvider
from app.schemas.call_attempt import CallAttemptListResponse, CallAttemptRead
from app.schemas.voice import RetryFailedResponse
from app.services.calls import dispatch_call_attempt
from app.services.retries import retry_failed_attempts

router = APIRouter(prefix="/call-attempts", tags=["call-attempts"])


@router.get("", response_model=CallAttemptListResponse)
def list_call_attempts(
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> CallAttemptListResponse:
    items = db.scalars(
        select(CallAttempt)
        .order_by(CallAttempt.requested_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    total = db.scalar(select(func.count()).select_from(CallAttempt)) or 0
    return CallAttemptListResponse(
        items=[CallAttemptRead.model_validate(item) for item in items],
        total=total,
    )


@router.post("/{attempt_id}/dispatch", response_model=CallAttemptRead)
async def dispatch_attempt(
    attempt_id: int,
    db: Session = Depends(get_db),
    telephony_provider: TelephonyProvider = Depends(get_telephony_provider),
) -> CallAttemptRead:
    attempt = db.get(CallAttempt, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="Call attempt not found")

    dispatched = await dispatch_call_attempt(
        db=db,
        attempt_id=attempt_id,
        telephony_provider=telephony_provider,
    )
    return CallAttemptRead.model_validate(dispatched)


@router.post("/retry-failed", response_model=RetryFailedResponse)
def retry_failed(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> RetryFailedResponse:
    created_ids, skipped_ids = retry_failed_attempts(
        db=db,
        max_retry_attempts_per_lead=settings.max_retry_attempts_per_lead,
    )
    return RetryFailedResponse(created_attempt_ids=created_ids, skipped_lead_ids=skipped_ids)
