from __future__ import annotations

import asyncio
import json
from base64 import b64encode

from app.core.config import Settings
from app.services.audio import chunk_frames

# NOTE: Sarvam's streaming STT WebSocket frame shape should be confirmed against their current
# docs at integration time. The protocol details are isolated to this module so the rest of the
# pipeline (the Exotel bridge) does not change when they are adjusted.


async def _stream_transcribe(
    settings: Settings,
    *,
    pcm: bytes,
    sample_rate: int,
    language: str,
) -> str:
    import websockets

    headers = {"api-subscription-key": settings.sarvam_api_key or ""}
    transcripts: list[str] = []
    async with websockets.connect(
        settings.sarvam_stt_ws_url, additional_headers=headers, open_timeout=10
    ) as ws:
        # 1) configure the stream
        await ws.send(
            json.dumps(
                {
                    "event": "start",
                    "model": settings.sarvam_stt_model,
                    "language_code": language,
                    "sample_rate": sample_rate,
                    "encoding": "audio/x-raw",
                }
            )
        )
        # 2) stream the audio in ~20ms frames, then signal end-of-stream
        for frame in chunk_frames(pcm):
            await ws.send(
                json.dumps({"event": "audio", "audio": b64encode(frame).decode("ascii")})
            )
        await ws.send(json.dumps({"event": "stop"}))

        # 3) collect transcripts until the socket reports completion / closes
        try:
            async for raw in ws:
                msg = json.loads(raw)
                text = msg.get("transcript") or msg.get("text")
                if text:
                    transcripts.append(text)
                if msg.get("type") in {"final", "complete"} or msg.get("event") == "stop":
                    break
        except Exception:
            pass

    return " ".join(t.strip() for t in transcripts if t).strip()


def transcribe_streaming_sync(
    settings: Settings,
    *,
    pcm: bytes,
    sample_rate: int,
    language: str,
) -> str:
    """Blocking wrapper so the (threadpool-run) Exotel bridge can use streaming STT.

    Raises on connection/protocol errors; the caller falls back to REST STT.
    """
    if not settings.sarvam_api_key:
        raise RuntimeError("SARVAM_API_KEY is required for streaming STT")
    return asyncio.run(
        _stream_transcribe(settings, pcm=pcm, sample_rate=sample_rate, language=language)
    )
