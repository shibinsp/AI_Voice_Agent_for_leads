from __future__ import annotations

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.db.session import get_session_factory
from app.services.auth import AuthError, verify_access_token
from app.services.voice import (
    complete_voice_session,
    get_voice_session,
    process_stream_audio,
    process_stream_text,
)

router = APIRouter(tags=["voice-stream"])

# WebSocket close codes
_POLICY_VIOLATION = 1008
_INTERNAL_ERROR = 1011


def _authorize(token: str | None, session_id: int) -> bool:
    """Operator tokens may open any session; an enquiry token (subject ``enquiry:<id>``) may
    open only its own session, so the public enquiry WS is safe without an operator login."""
    settings = get_settings()
    if not settings.auth_enabled:
        return True
    if not token:
        return False
    try:
        subject = verify_access_token(settings, token)
    except AuthError:
        return False
    if subject.startswith("enquiry:"):
        return subject == f"enquiry:{session_id}"
    return True


@router.websocket("/voice-sessions/{session_id}/stream")
async def voice_session_stream(
    websocket: WebSocket,
    session_id: int,
    token: str | None = Query(default=None),
) -> None:
    """Live STT -> LLM -> TTS loop for one voice session.

    Browsers cannot set WebSocket headers, so the bearer token is passed as a query param.
    Protocol (JSON frames):
      in  {"type": "text", "text": "...", "confidence": 0.9}   # browser STT (Web Speech API)
      in  {"type": "audio", "audio_base64": "...", "mime_type": "audio/webm"}  # server-side STT
      out {"type": "turn", "lead_text", "agent_text", ["agent_audio_base64", "mime_type"]}
      in  {"type": "end"}
      out {"type": "completed", "qualification": {...}}
    """
    if not _authorize(token, session_id):
        await websocket.close(code=_POLICY_VIOLATION)
        return

    session_factory = get_session_factory()
    db = session_factory()
    try:
        session = get_voice_session(db, session_id)
        if session is None:
            await websocket.close(code=_POLICY_VIOLATION)
            return

        await websocket.accept()
        await websocket.send_json(
            {"type": "ready", "session_id": session_id, "language": session.language}
        )

        while True:
            message = await websocket.receive_json()
            msg_type = message.get("type")

            if msg_type == "text":
                result = await run_in_threadpool(
                    process_stream_text,
                    db,
                    session_id=session_id,
                    lead_text=message.get("text", ""),
                    confidence=message.get("confidence"),
                )
                await websocket.send_json({"type": "turn", **result})

            elif msg_type == "audio":
                result = await run_in_threadpool(
                    process_stream_audio,
                    db,
                    session_id=session_id,
                    audio_base64=message.get("audio_base64", ""),
                    mime_type=message.get("mime_type", "audio/wav"),
                )
                await websocket.send_json({"type": "turn", **result})

            elif msg_type == "end":
                completed = await run_in_threadpool(
                    complete_voice_session, db, session_id=session_id
                )
                qr = completed.qualification_result
                await websocket.send_json(
                    {
                        "type": "completed",
                        "session_id": session_id,
                        "qualification": {
                            "outcome": qr.outcome.value,
                            "score": qr.score,
                            "summary": qr.summary,
                        }
                        if qr
                        else None,
                    }
                )
                await websocket.close()
                return

            else:
                await websocket.send_json(
                    {"type": "error", "detail": f"Unknown message type: {msg_type!r}"}
                )

    except WebSocketDisconnect:
        return
    except ValueError as exc:
        await _safe_send_error(websocket, str(exc))
    except Exception as exc:  # noqa: BLE001 - surface provider failures to the client
        await _safe_send_error(websocket, f"stream error: {exc}", code=_INTERNAL_ERROR)
    finally:
        db.close()


async def _safe_send_error(websocket: WebSocket, detail: str, code: int = _POLICY_VIOLATION) -> None:
    try:
        await websocket.send_json({"type": "error", "detail": detail})
        await websocket.close(code=code)
    except (WebSocketDisconnect, RuntimeError):
        return
