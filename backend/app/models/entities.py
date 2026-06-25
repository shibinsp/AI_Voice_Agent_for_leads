from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class LeadStatus(StrEnum):
    NEW = "new"
    CALL_QUEUED = "call_queued"
    CALLING = "calling"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    NOT_QUALIFIED = "not_qualified"
    CALLBACK_REQUESTED = "callback_requested"
    FAILED = "failed"


class CallAttemptStatus(StrEnum):
    QUEUED = "queued"
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BUSY = "busy"
    NO_ANSWER = "no_answer"
    FAILED = "failed"


class VoiceSessionStatus(StrEnum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class TranscriptSpeaker(StrEnum):
    AGENT = "agent"
    LEAD = "lead"
    SYSTEM = "system"


class QualificationOutcome(StrEnum):
    QUALIFIED = "qualified"
    NOT_QUALIFIED = "not_qualified"
    CALLBACK_REQUESTED = "callback_requested"
    NEEDS_REVIEW = "needs_review"


class HandoffStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Client(TimestampMixin, Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    vertical: Mapped[str | None] = mapped_column(String(120))
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    campaigns: Mapped[list[Campaign]] = relationship(back_populates="client")
    leads: Mapped[list[Lead]] = relationship(back_populates="client")


class Agent(TimestampMixin, Base):
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    script_key: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    vertical: Mapped[str | None] = mapped_column(String(120))
    language: Mapped[str] = mapped_column(String(20), default="te-IN", nullable=False)
    voice_provider: Mapped[str] = mapped_column(String(60), default="sarvam", nullable=False)
    telephony_provider: Mapped[str] = mapped_column(String(60), default="mock", nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    opening_line: Mapped[str | None] = mapped_column(Text)
    qualification_goal: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    voice_sessions: Mapped[list[VoiceSession]] = relationship(back_populates="agent")


class Campaign(TimestampMixin, Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id"))
    external_form_id: Mapped[str | None] = mapped_column(String(120), unique=True)
    external_campaign_id: Mapped[str | None] = mapped_column(String(120))
    name: Mapped[str | None] = mapped_column(String(255))
    script_key: Mapped[str] = mapped_column(String(120), default="default_v1", nullable=False)
    language: Mapped[str] = mapped_column(String(20), default="te-IN", nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    client: Mapped[Client | None] = relationship(back_populates="campaigns")
    leads: Mapped[list[Lead]] = relationship(back_populates="campaign")


class Lead(TimestampMixin, Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id"))
    campaign_id: Mapped[int | None] = mapped_column(ForeignKey("campaigns.id"))
    external_lead_id: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    external_page_id: Mapped[str | None] = mapped_column(String(120))
    full_name: Mapped[str | None] = mapped_column(String(255))
    phone_number: Mapped[str | None] = mapped_column(String(32))
    email: Mapped[str | None] = mapped_column(String(255))
    preferred_language: Mapped[str] = mapped_column(String(20), default="te-IN", nullable=False)
    city: Mapped[str | None] = mapped_column(String(120))
    raw_fields: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    raw_event: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus),
        default=LeadStatus.CALL_QUEUED,
        nullable=False,
    )

    client: Mapped[Client | None] = relationship(back_populates="leads")
    campaign: Mapped[Campaign | None] = relationship(back_populates="leads")
    call_attempts: Mapped[list[CallAttempt]] = relationship(
        back_populates="lead",
        cascade="all, delete-orphan",
    )
    voice_sessions: Mapped[list[VoiceSession]] = relationship(back_populates="lead")
    qualification_results: Mapped[list[QualificationResult]] = relationship(back_populates="lead")
    handoff_events: Mapped[list[HandoffEvent]] = relationship(back_populates="lead")


class CallAttempt(Base):
    __tablename__ = "call_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(40), default="mock", nullable=False)
    script_key: Mapped[str] = mapped_column(String(120), default="default_v1", nullable=False)
    phone_number: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_call_id: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[CallAttemptStatus] = mapped_column(
        Enum(CallAttemptStatus),
        default=CallAttemptStatus.QUEUED,
        nullable=False,
    )
    failure_reason: Mapped[str | None] = mapped_column(Text)
    provider_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    lead: Mapped[Lead] = relationship(back_populates="call_attempts")
    voice_sessions: Mapped[list[VoiceSession]] = relationship(
        back_populates="call_attempt",
        cascade="all, delete-orphan",
    )


class VoiceSession(Base):
    __tablename__ = "voice_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    call_attempt_id: Mapped[int] = mapped_column(ForeignKey("call_attempts.id"), nullable=False)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), nullable=False)
    agent_id: Mapped[int | None] = mapped_column(ForeignKey("agents.id"))
    status: Mapped[VoiceSessionStatus] = mapped_column(
        Enum(VoiceSessionStatus),
        default=VoiceSessionStatus.CREATED,
        nullable=False,
    )
    language: Mapped[str] = mapped_column(String(20), default="te-IN", nullable=False)
    audio_stream_url: Mapped[str | None] = mapped_column(Text)
    session_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    call_attempt: Mapped[CallAttempt] = relationship(back_populates="voice_sessions")
    lead: Mapped[Lead] = relationship(back_populates="voice_sessions")
    agent: Mapped[Agent | None] = relationship(back_populates="voice_sessions")
    transcript_turns: Mapped[list[TranscriptTurn]] = relationship(
        back_populates="voice_session",
        cascade="all, delete-orphan",
    )
    qualification_result: Mapped[QualificationResult | None] = relationship(
        back_populates="voice_session",
        cascade="all, delete-orphan",
    )


class TranscriptTurn(Base):
    __tablename__ = "transcript_turns"

    id: Mapped[int] = mapped_column(primary_key=True)
    voice_session_id: Mapped[int] = mapped_column(ForeignKey("voice_sessions.id"), nullable=False)
    speaker: Mapped[TranscriptSpeaker] = mapped_column(Enum(TranscriptSpeaker), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)
    turn_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    voice_session: Mapped[VoiceSession] = relationship(back_populates="transcript_turns")


class QualificationResult(Base):
    __tablename__ = "qualification_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    voice_session_id: Mapped[int] = mapped_column(
        ForeignKey("voice_sessions.id"),
        unique=True,
        nullable=False,
    )
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), nullable=False)
    outcome: Mapped[QualificationOutcome] = mapped_column(Enum(QualificationOutcome), nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    fields: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    voice_session: Mapped[VoiceSession] = relationship(back_populates="qualification_result")
    lead: Mapped[Lead] = relationship(back_populates="qualification_results")
    handoff_events: Mapped[list[HandoffEvent]] = relationship(
        back_populates="qualification_result",
        cascade="all, delete-orphan",
    )


class HandoffEvent(Base):
    __tablename__ = "handoff_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    qualification_result_id: Mapped[int] = mapped_column(
        ForeignKey("qualification_results.id"),
        nullable=False,
    )
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), nullable=False)
    channel: Mapped[str] = mapped_column(String(40), nullable=False)
    destination: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[HandoffStatus] = mapped_column(
        Enum(HandoffStatus),
        default=HandoffStatus.PENDING,
        nullable=False,
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    response_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    qualification_result: Mapped[QualificationResult] = relationship(
        back_populates="handoff_events"
    )
    lead: Mapped[Lead] = relationship(back_populates="handoff_events")
