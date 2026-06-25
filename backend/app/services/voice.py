from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.entities import (
    Agent,
    CallAttempt,
    CallAttemptStatus,
    LeadStatus,
    QualificationResult,
    TranscriptSpeaker,
    TranscriptTurn,
    VoiceSession,
    VoiceSessionStatus,
)
from app.core.config import get_settings
from app.providers.speech.factory import build_speech_provider
from app.schemas.voice import TranscriptTurnCreate
from app.services.dialogue import next_agent_reply, opening_line_for
from app.services.handoffs import create_handoff_for_qualification
from app.services.llm_dialogue import generate_agent_reply, qualify_with_llm


def _now() -> datetime:
    return datetime.now(timezone.utc)


def list_voice_sessions(db: Session, *, limit: int, offset: int) -> tuple[list[VoiceSession], int]:
    query = (
        select(VoiceSession)
        .options(
            selectinload(VoiceSession.transcript_turns),
            selectinload(VoiceSession.qualification_result),
        )
        .order_by(VoiceSession.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    items = db.scalars(query).all()
    total = db.scalar(select(func.count()).select_from(VoiceSession)) or 0
    return list(items), total


def get_voice_session(db: Session, session_id: int) -> VoiceSession | None:
    return db.scalar(
        select(VoiceSession)
        .where(VoiceSession.id == session_id)
        .options(
            selectinload(VoiceSession.transcript_turns),
            selectinload(VoiceSession.qualification_result),
        )
    )


def start_voice_session(db: Session, *, call_attempt_id: int) -> VoiceSession:
    attempt = db.get(CallAttempt, call_attempt_id)
    if attempt is None:
        raise ValueError("Call attempt not found")

    existing = db.scalar(
        select(VoiceSession)
        .where(VoiceSession.call_attempt_id == call_attempt_id)
        .options(
            selectinload(VoiceSession.transcript_turns),
            selectinload(VoiceSession.qualification_result),
        )
    )
    if existing is not None:
        return existing

    agent = _find_agent_for_attempt(db, attempt)
    session = VoiceSession(
        call_attempt_id=attempt.id,
        lead_id=attempt.lead_id,
        agent_id=agent.id if agent else None,
        status=VoiceSessionStatus.IN_PROGRESS,
        language=agent.language if agent else attempt.lead.preferred_language,
        audio_stream_url=attempt.provider_payload.get("stream_url")
        if isinstance(attempt.provider_payload, dict)
        else None,
        session_metadata={
            "script_key": attempt.script_key,
            "provider": attempt.provider,
            "mode": "demo" if attempt.provider == "mock" else "live",
        },
        started_at=_now(),
    )
    attempt.status = CallAttemptStatus.IN_PROGRESS
    attempt.lead.status = LeadStatus.CALLING
    db.add(session)
    db.flush()
    db.add(
        TranscriptTurn(
            voice_session_id=session.id,
            speaker=TranscriptSpeaker.AGENT,
            text=opening_line_for(agent, attempt.lead),
            confidence=1.0,
            turn_metadata={"source": "agent_opening"},
        )
    )
    db.commit()
    return get_voice_session(db, session.id) or session


def add_transcript_turn(
    db: Session,
    *,
    session_id: int,
    payload: TranscriptTurnCreate,
) -> VoiceSession:
    session = get_voice_session(db, session_id)
    if session is None:
        raise ValueError("Voice session not found")
    if session.status != VoiceSessionStatus.IN_PROGRESS:
        raise ValueError("Voice session is not in progress")

    db.add(
        TranscriptTurn(
            voice_session_id=session.id,
            speaker=payload.speaker,
            text=payload.text,
            confidence=payload.confidence,
            turn_metadata=payload.turn_metadata,
        )
    )
    db.commit()
    return get_voice_session(db, session_id) or session


def complete_voice_session(db: Session, *, session_id: int) -> VoiceSession:
    session = get_voice_session(db, session_id)
    if session is None:
        raise ValueError("Voice session not found")
    if session.qualification_result is not None:
        return session

    agent = session.agent
    decision = qualify_with_llm(
        get_settings(),
        agent=agent,
        lead=session.lead,
        turns=session.transcript_turns,
    )
    qualification = QualificationResult(
        voice_session_id=session.id,
        lead_id=session.lead_id,
        outcome=decision.outcome,
        score=decision.score,
        summary=decision.summary,
        fields=decision.fields,
    )
    db.add(qualification)
    session.status = VoiceSessionStatus.COMPLETED
    session.ended_at = _now()
    session.call_attempt.status = CallAttemptStatus.COMPLETED
    session.call_attempt.completed_at = session.ended_at
    session.lead.status = _lead_status_for_outcome(decision.outcome.value)
    db.add(session)
    db.flush()
    create_handoff_for_qualification(db=db, qualification=qualification)
    return get_voice_session(db, session_id) or session


def process_stream_audio(
    db: Session,
    *,
    session_id: int,
    audio_base64: str,
    mime_type: str,
) -> dict:
    """One streamed turn: STT on the lead audio, LLM agent reply, TTS on the reply.

    Persists a LEAD turn and an AGENT turn and returns the texts plus synthesized reply audio.
    Synchronous on purpose (blocking provider HTTP); the WebSocket route off-loads it to a
    threadpool so the event loop stays responsive.
    """
    session = get_voice_session(db, session_id)
    if session is None:
        raise ValueError("Voice session not found")
    if session.status != VoiceSessionStatus.IN_PROGRESS:
        raise ValueError("Voice session is not in progress")

    settings = get_settings()
    speech = build_speech_provider(settings)

    transcription = speech.transcribe(
        audio_base64=audio_base64,
        mime_type=mime_type or "audio/wav",
        language=session.language,
    )
    lead_text = transcription.text or "(unintelligible)"
    add_transcript_turn(
        db,
        session_id=session_id,
        payload=TranscriptTurnCreate(
            speaker=TranscriptSpeaker.LEAD,
            text=lead_text,
            confidence=transcription.confidence,
            turn_metadata={"source": "stt", "provider": speech.name},
        ),
    )

    session = get_voice_session(db, session_id)
    agent_text = generate_agent_reply(
        settings,
        agent=session.agent,
        lead=session.lead,
        turns=list(session.transcript_turns),
    )
    add_transcript_turn(
        db,
        session_id=session_id,
        payload=TranscriptTurnCreate(
            speaker=TranscriptSpeaker.AGENT,
            text=agent_text,
            confidence=1.0,
            turn_metadata={"source": "llm", "provider": settings.llm_provider},
        ),
    )

    synthesis = speech.synthesize(text=agent_text, language=session.language)
    return {
        "lead_text": lead_text,
        "lead_confidence": transcription.confidence,
        "agent_text": agent_text,
        "agent_audio_base64": synthesis.audio_base64,
        "mime_type": synthesis.mime_type,
    }


def process_stream_text(
    db: Session,
    *,
    session_id: int,
    lead_text: str,
    confidence: float | None = None,
) -> dict:
    """One streamed turn when STT/TTS happen in the browser (Web Speech API).

    The browser sends the already-transcribed lead utterance; we persist it, generate the
    agent reply via the LLM, persist that, and return the texts. Audio never crosses the wire.
    """
    session = get_voice_session(db, session_id)
    if session is None:
        raise ValueError("Voice session not found")
    if session.status != VoiceSessionStatus.IN_PROGRESS:
        raise ValueError("Voice session is not in progress")

    text = (lead_text or "").strip() or "(unintelligible)"
    add_transcript_turn(
        db,
        session_id=session_id,
        payload=TranscriptTurnCreate(
            speaker=TranscriptSpeaker.LEAD,
            text=text,
            confidence=confidence,
            turn_metadata={"source": "browser_stt"},
        ),
    )

    session = get_voice_session(db, session_id)
    settings = get_settings()
    agent_text = generate_agent_reply(
        settings,
        agent=session.agent,
        lead=session.lead,
        turns=list(session.transcript_turns),
    )
    add_transcript_turn(
        db,
        session_id=session_id,
        payload=TranscriptTurnCreate(
            speaker=TranscriptSpeaker.AGENT,
            text=agent_text,
            confidence=1.0,
            turn_metadata={"source": "llm", "provider": settings.llm_provider},
        ),
    )
    return {"lead_text": text, "lead_confidence": confidence, "agent_text": agent_text}


def run_demo_voice_session(db: Session, *, call_attempt_id: int) -> VoiceSession:
    session = start_voice_session(db, call_attempt_id=call_attempt_id)
    if session.qualification_result is not None:
        return session

    agent = session.agent
    demo_lead_text = _demo_lead_text(agent)
    db.add(
        TranscriptTurn(
            voice_session_id=session.id,
            speaker=TranscriptSpeaker.LEAD,
            text=demo_lead_text,
            confidence=0.91,
            turn_metadata={"source": "demo_lead"},
        )
    )
    db.flush()
    turns = list(session.transcript_turns)
    db.add(
        TranscriptTurn(
            voice_session_id=session.id,
            speaker=TranscriptSpeaker.AGENT,
            text=next_agent_reply(agent, session.lead, turns),
            confidence=1.0,
            turn_metadata={"source": "demo_agent"},
        )
    )
    db.add(
        TranscriptTurn(
            voice_session_id=session.id,
            speaker=TranscriptSpeaker.LEAD,
            text="Please arrange a callback today after 5 PM.",
            confidence=0.88,
            turn_metadata={"source": "demo_lead"},
        )
    )
    db.commit()
    return complete_voice_session(db, session_id=session.id)


def _find_agent_for_attempt(db: Session, attempt: CallAttempt) -> Agent | None:
    agent = db.scalar(select(Agent).where(Agent.script_key == attempt.script_key))
    if agent is not None:
        return agent
    return db.scalar(select(Agent).where(Agent.is_active.is_(True)).order_by(Agent.updated_at.desc()))


def _demo_lead_text(agent: Agent | None) -> str:
    vertical = agent.vertical if agent else None
    if vertical == "real_estate":
        return "I am interested in a 2 BHK near Gachibowli and my budget is around 90 lakhs."
    if vertical == "education":
        return "I want details for the weekend demo class and admission fees."
    if vertical == "insurance":
        return "I need a callback about term insurance options."
    return "I am interested in booking an appointment this week."


def _lead_status_for_outcome(outcome: str) -> LeadStatus:
    if outcome == "qualified":
        return LeadStatus.QUALIFIED
    if outcome == "callback_requested":
        return LeadStatus.CALLBACK_REQUESTED
    if outcome == "not_qualified":
        return LeadStatus.NOT_QUALIFIED
    return LeadStatus.CONTACTED
