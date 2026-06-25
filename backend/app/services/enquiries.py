from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.entities import (
    Agent,
    CallAttempt,
    CallAttemptStatus,
    Lead,
    LeadStatus,
)
from app.schemas.enquiry import EnquiryCreate
from app.services.auth import create_access_token
from app.services.leads import _normalize_phone
from app.services.voice import start_voice_session

DEFAULT_SCRIPT_KEY = "default_v1"


@dataclass(slots=True)
class EnquiryResult:
    lead_id: int
    session_id: int
    token: str
    language: str
    opening_line: str


def create_enquiry(db: Session, *, payload: EnquiryCreate, settings: Settings) -> EnquiryResult:
    """Public self-serve enquiry: create the lead + a web call attempt + an in-progress voice
    session, and mint a session-scoped token so the prospect's browser can drive the call WS
    without an operator login."""
    agent = db.scalar(
        select(Agent).where(Agent.is_active.is_(True)).order_by(Agent.updated_at.desc())
    )
    script_key = agent.script_key if agent else DEFAULT_SCRIPT_KEY
    language = payload.language or (agent.language if agent else "te-IN")

    lead = Lead(
        external_lead_id=f"enq-{uuid4().hex}",
        full_name=payload.full_name,
        phone_number=_normalize_phone(payload.phone_number),
        email=payload.email,
        city=payload.city,
        preferred_language=language,
        raw_fields={
            "requirement": payload.requirement,
            "source": payload.source,
            "channel": "enquiry_link",
        },
        raw_event={},
        status=LeadStatus.CALL_QUEUED,
    )
    db.add(lead)
    db.flush()

    attempt = CallAttempt(
        lead_id=lead.id,
        provider="web",
        script_key=script_key,
        phone_number=lead.phone_number or "web",
        status=CallAttemptStatus.INITIATED,
        provider_payload={"channel": "enquiry_link"},
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    session = start_voice_session(db, call_attempt_id=attempt.id)
    opening_line = next(
        (turn.text for turn in session.transcript_turns if turn.speaker.value == "agent"),
        "Namaskaram!",
    )

    token, _ = create_access_token(
        settings,
        subject=f"enquiry:{session.id}",
        expires_in_minutes=settings.enquiry_token_expire_minutes,
    )

    return EnquiryResult(
        lead_id=lead.id,
        session_id=session.id,
        token=token,
        language=session.language,
        opening_line=opening_line,
    )
