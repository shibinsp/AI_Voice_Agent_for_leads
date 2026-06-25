from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.entities import (
    CallAttempt,
    HandoffEvent,
    HandoffStatus,
    Lead,
    QualificationOutcome,
    QualificationResult,
    VoiceSession,
    VoiceSessionStatus,
)

GENUINE_OUTCOMES = {QualificationOutcome.QUALIFIED, QualificationOutcome.CALLBACK_REQUESTED}


def _count_by(db: Session, column) -> dict[str, int]:
    rows = db.execute(select(column, func.count()).group_by(column)).all()
    out: dict[str, int] = {}
    for key, n in rows:
        out[getattr(key, "value", str(key))] = n
    return out


def build_analytics_summary(db: Session) -> dict[str, Any]:
    leads_total = db.scalar(select(func.count()).select_from(Lead)) or 0
    attempts_total = db.scalar(select(func.count()).select_from(CallAttempt)) or 0
    sessions_total = db.scalar(select(func.count()).select_from(VoiceSession)) or 0
    sessions_completed = (
        db.scalar(
            select(func.count())
            .select_from(VoiceSession)
            .where(VoiceSession.status == VoiceSessionStatus.COMPLETED)
        )
        or 0
    )
    qual_total = db.scalar(select(func.count()).select_from(QualificationResult)) or 0
    outcomes = _count_by(db, QualificationResult.outcome)
    genuine = sum(outcomes.get(o.value, 0) for o in GENUINE_OUTCOMES)
    avg_score = db.scalar(select(func.avg(QualificationResult.score)))
    handoffs_total = db.scalar(select(func.count()).select_from(HandoffEvent)) or 0
    handoffs_sent = (
        db.scalar(
            select(func.count())
            .select_from(HandoffEvent)
            .where(HandoffEvent.status == HandoffStatus.SENT)
        )
        or 0
    )

    return {
        "enquiries": {"total": leads_total, "by_status": _count_by(db, Lead.status)},
        "calls": {"total": attempts_total, "by_status": _count_by(db, CallAttempt.status)},
        "sessions": {"total": sessions_total, "completed": sessions_completed},
        "qualification": {
            "total": qual_total,
            "by_outcome": outcomes,
            "genuine": genuine,
            "genuine_rate": round(genuine / qual_total, 3) if qual_total else 0.0,
            "avg_score": round(float(avg_score), 1) if avg_score is not None else 0.0,
        },
        "handoffs": {"total": handoffs_total, "sent": handoffs_sent},
    }
