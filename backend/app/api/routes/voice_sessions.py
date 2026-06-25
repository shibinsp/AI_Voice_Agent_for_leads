from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.voice import TranscriptTurnCreate, VoiceSessionListResponse, VoiceSessionRead
from app.services.voice import (
    add_transcript_turn,
    complete_voice_session,
    get_voice_session,
    list_voice_sessions,
    run_demo_voice_session,
    start_voice_session,
)

router = APIRouter(prefix="/voice-sessions", tags=["voice-sessions"])


@router.get("", response_model=VoiceSessionListResponse)
def get_voice_sessions(
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> VoiceSessionListResponse:
    items, total = list_voice_sessions(db, limit=limit, offset=offset)
    return VoiceSessionListResponse(
        items=[VoiceSessionRead.model_validate(item) for item in items],
        total=total,
    )


@router.get("/{session_id}", response_model=VoiceSessionRead)
def read_voice_session(session_id: int, db: Session = Depends(get_db)) -> VoiceSessionRead:
    session = get_voice_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Voice session not found")
    return VoiceSessionRead.model_validate(session)


@router.post("/from-call-attempt/{attempt_id}", response_model=VoiceSessionRead)
def create_voice_session(attempt_id: int, db: Session = Depends(get_db)) -> VoiceSessionRead:
    try:
        session = start_voice_session(db, call_attempt_id=attempt_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return VoiceSessionRead.model_validate(session)


@router.post("/from-call-attempt/{attempt_id}/demo", response_model=VoiceSessionRead)
def run_demo_session(attempt_id: int, db: Session = Depends(get_db)) -> VoiceSessionRead:
    try:
        session = run_demo_voice_session(db, call_attempt_id=attempt_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return VoiceSessionRead.model_validate(session)


@router.post("/{session_id}/turns", response_model=VoiceSessionRead)
def create_transcript_turn(
    session_id: int,
    payload: TranscriptTurnCreate,
    db: Session = Depends(get_db),
) -> VoiceSessionRead:
    try:
        session = add_transcript_turn(db, session_id=session_id, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return VoiceSessionRead.model_validate(session)


@router.post("/{session_id}/complete", response_model=VoiceSessionRead)
def finish_voice_session(session_id: int, db: Session = Depends(get_db)) -> VoiceSessionRead:
    try:
        session = complete_voice_session(db, session_id=session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return VoiceSessionRead.model_validate(session)
