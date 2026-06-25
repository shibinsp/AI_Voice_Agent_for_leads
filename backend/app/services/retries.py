from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import CallAttempt, CallAttemptStatus, LeadStatus


def retry_failed_attempts(
    *,
    db: Session,
    max_retry_attempts_per_lead: int,
) -> tuple[list[int], list[int]]:
    failed_attempts = db.scalars(
        select(CallAttempt).where(
            CallAttempt.status.in_(
                [
                    CallAttemptStatus.FAILED,
                    CallAttemptStatus.BUSY,
                    CallAttemptStatus.NO_ANSWER,
                ]
            )
        )
    ).all()

    created_ids: list[int] = []
    skipped_lead_ids: list[int] = []
    for attempt in failed_attempts:
        attempts_for_lead = db.scalars(
            select(CallAttempt).where(CallAttempt.lead_id == attempt.lead_id)
        ).all()
        if len(attempts_for_lead) > max_retry_attempts_per_lead:
            skipped_lead_ids.append(attempt.lead_id)
            continue
        if any(
            item.status
            in {
                CallAttemptStatus.QUEUED,
                CallAttemptStatus.INITIATED,
                CallAttemptStatus.IN_PROGRESS,
            }
            and item.id != attempt.id
            for item in attempts_for_lead
        ):
            skipped_lead_ids.append(attempt.lead_id)
            continue

        retry = CallAttempt(
            lead_id=attempt.lead_id,
            provider="pending",
            script_key=attempt.script_key,
            phone_number=attempt.phone_number,
            status=CallAttemptStatus.QUEUED,
            provider_payload={"retry_of": attempt.id},
        )
        attempt.lead.status = LeadStatus.CALL_QUEUED
        db.add(retry)
        db.flush()
        created_ids.append(retry.id)

    db.commit()
    return created_ids, skipped_lead_ids
