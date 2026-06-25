from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.entities import (
    HandoffStatus,
    QualificationOutcome,
    TranscriptSpeaker,
    VoiceSessionStatus,
)


class TranscriptTurnCreate(BaseModel):
    speaker: TranscriptSpeaker
    text: str = Field(min_length=1)
    confidence: float | None = Field(default=None, ge=0, le=1)
    turn_metadata: dict[str, Any] = Field(default_factory=dict)


class TranscriptTurnRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    voice_session_id: int
    speaker: TranscriptSpeaker
    text: str
    confidence: float | None
    turn_metadata: dict[str, Any]
    created_at: datetime


class QualificationResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    voice_session_id: int
    lead_id: int
    outcome: QualificationOutcome
    score: int
    summary: str
    fields: dict[str, Any]
    created_at: datetime


class HandoffEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    qualification_result_id: int
    lead_id: int
    channel: str
    destination: str
    status: HandoffStatus
    payload: dict[str, Any]
    response_payload: dict[str, Any]
    failure_reason: str | None
    created_at: datetime
    sent_at: datetime | None


class VoiceSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    call_attempt_id: int
    lead_id: int
    agent_id: int | None
    status: VoiceSessionStatus
    language: str
    audio_stream_url: str | None
    session_metadata: dict[str, Any]
    started_at: datetime | None
    ended_at: datetime | None
    created_at: datetime
    transcript_turns: list[TranscriptTurnRead] = []
    qualification_result: QualificationResultRead | None = None


class VoiceSessionListResponse(BaseModel):
    items: list[VoiceSessionRead]
    total: int


class HandoffListResponse(BaseModel):
    items: list[HandoffEventRead]
    total: int


class IntegrationReadiness(BaseModel):
    auth: bool
    meta: bool
    telephony: bool
    sarvam: bool
    llm: bool
    crm: bool
    handoff: bool
    missing: list[str]


class RetryFailedResponse(BaseModel):
    created_attempt_ids: list[int]
    skipped_lead_ids: list[int]
