from __future__ import annotations

import hmac

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.config import get_settings
from app.db.session import get_session_factory
from app.services.exotel_stream import (
    EVENT_MEDIA,
    EVENT_START,
    EVENT_STOP,
    ExotelCallBridge,
)

router = APIRouter(tags=["telephony-stream"])

_POLICY_VIOLATION = 1008


def _authorize(token: str | None) -> bool:
    """Exotel cannot send auth headers, so the StreamUrl carries a shared secret query token."""
    settings = get_settings()
    secret = settings.exotel_stream_secret
    if not secret:
        # No secret configured -> only allow when auth is disabled (local/dev), never in prod.
        return not settings.auth_enabled
    if not token:
        return False
    return hmac.compare_digest(token, secret)


@router.websocket("/telephony/exotel/stream")
async def exotel_media_stream(
    websocket: WebSocket,
    token: str | None = Query(default=None),
) -> None:
    """Receives Exotel's bidirectional media stream for a live call and drives the AI conversation.

    Protocol frames (JSON): connected | start | media | stop. Inbound `media` carries base64 8 kHz
    PCM from the caller; we stream synthesized agent audio back as `media` frames.
    """
    if not _authorize(token):
        await websocket.close(code=_POLICY_VIOLATION)
        return

    await websocket.accept()
    db = get_session_factory()()
    bridge = ExotelCallBridge(db, get_settings(), websocket.send_json)
    try:
        while True:
            message = await websocket.receive_json()
            event = message.get("event")
            if event == EVENT_START:
                await bridge.on_start(message)
            elif event == EVENT_MEDIA:
                await bridge.on_media(message)
            elif event in (EVENT_STOP, "disconnect"):
                await bridge.on_stop()
                break
            # `connected`, `dtmf`, `mark`, etc. are ignored for now
    except WebSocketDisconnect:
        await bridge.on_stop()
    except Exception:
        await bridge.on_stop()
    finally:
        db.close()
        try:
            await websocket.close()
        except RuntimeError:
            pass
