from __future__ import annotations

from base64 import b64decode, b64encode
from collections.abc import Awaitable, Callable
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.core.config import Settings
from app.models.entities import CallAttempt
from app.providers.speech.factory import build_speech_provider
from app.services.audio import (
    UtteranceVAD,
    chunk_frames,
    wav_to_pcm,
    wrap_pcm_as_wav,
)
from app.services.voice import (
    complete_voice_session,
    get_voice_session,
    process_stream_text,
    start_voice_session,
)

# Exotel voicebot media-stream events. NOTE: the exact frame key names should be reconciled
# against Exotel's current bidirectional-streaming docs at integration time — they are read
# defensively here (snake_case + camelCase) and isolated to the extract helpers below.
EVENT_CONNECTED = "connected"
EVENT_START = "start"
EVENT_MEDIA = "media"
EVENT_STOP = "stop"
EVENT_DTMF = "dtmf"

SendFn = Callable[[dict[str, Any]], Awaitable[None]]


def _first(d: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if isinstance(d, dict) and d.get(key) not in (None, ""):
            return d[key]
    return None


def extract_start(message: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    """Return (call_sid, stream_sid, custom_field) from a `start` frame, tolerant of key casing."""
    start = message.get("start") if isinstance(message.get("start"), dict) else {}
    call_sid = _first(start, "call_sid", "callSid") or _first(message, "call_sid", "callSid")
    stream_sid = _first(message, "stream_sid", "streamSid") or _first(start, "stream_sid", "streamSid")
    custom = _first(start, "custom_field", "customField", "CustomField")
    return call_sid, stream_sid, custom


def extract_media_payload(message: dict[str, Any]) -> bytes | None:
    media = message.get("media") if isinstance(message.get("media"), dict) else {}
    payload = _first(media, "payload")
    if not payload:
        return None
    try:
        return b64decode(payload)
    except (ValueError, TypeError):
        return None


def _lead_id_from_custom(custom_field: str | None) -> int | None:
    if not custom_field or "lead:" not in custom_field:
        return None
    try:
        return int(custom_field.split("lead:", 1)[1].split(",")[0].strip())
    except (ValueError, IndexError):
        return None


class ExotelCallBridge:
    """Bridges one Exotel media-streamed phone call to the STT->LLM->TTS voice pipeline.

    Half-duplex: caller audio is segmented by VAD into utterances; each is transcribed, answered
    by the dialogue LLM, synthesized, and streamed back. Reuses the same VoiceSession/transcript/
    qualification/handoff path as the browser call.
    """

    def __init__(self, db: Session, settings: Settings, send: SendFn) -> None:
        self.db = db
        self.settings = settings
        self.send = send
        self.speech = build_speech_provider(settings)
        self.vad = UtteranceVAD(
            sample_rate=settings.phone_media_sample_rate,
            energy_threshold=settings.phone_vad_energy_threshold,
            silence_ms=settings.phone_vad_silence_ms,
        )
        self.session_id: int | None = None
        self.stream_sid: str | None = None
        self.started = False

    async def on_start(self, message: dict[str, Any]) -> None:
        call_sid, stream_sid, custom = extract_start(message)
        self.stream_sid = stream_sid
        session = await run_in_threadpool(self._start_session, call_sid, custom)
        if session is None:
            return
        self.session_id = session.id
        self.started = True
        opening = next(
            (t.text for t in session.transcript_turns if t.speaker.value == "agent"),
            None,
        )
        if opening:
            await self._speak(opening)

    async def on_media(self, message: dict[str, Any]) -> None:
        if not self.started or self.session_id is None:
            return
        pcm = extract_media_payload(message)
        if pcm is None:
            return
        utterance = self.vad.add_frame(pcm)
        if utterance is not None:
            await self._handle_utterance(utterance)

    async def on_stop(self) -> None:
        if self.session_id is None:
            return
        session_id = self.session_id
        self.session_id = None  # guard against double-complete
        await run_in_threadpool(self._complete, session_id)

    # --- internals (sync DB / provider work runs in a threadpool) ---

    def _start_session(self, call_sid: str | None, custom_field: str | None):
        attempt = None
        if call_sid:
            attempt = self.db.scalar(
                select(CallAttempt).where(CallAttempt.provider_call_id == call_sid)
            )
        if attempt is None:
            lead_id = _lead_id_from_custom(custom_field)
            if lead_id is not None:
                attempt = self.db.scalar(
                    select(CallAttempt)
                    .where(CallAttempt.lead_id == lead_id)
                    .order_by(CallAttempt.id.desc())
                )
        if attempt is None:
            return None
        return start_voice_session(self.db, call_attempt_id=attempt.id)

    def _transcribe_and_reply(self, utterance_pcm: bytes) -> str | None:
        wav = wrap_pcm_as_wav(utterance_pcm, sample_rate=self.settings.phone_media_sample_rate)
        transcription = self.speech.transcribe(
            audio_base64=b64encode(wav).decode("ascii"),
            mime_type="audio/wav",
            language=self._language(),
        )
        text = (transcription.text or "").strip()
        if not text:
            return None
        result = process_stream_text(
            self.db,
            session_id=self.session_id,
            lead_text=text,
            confidence=transcription.confidence,
        )
        return result["agent_text"]

    def _synthesize_pcm(self, text: str) -> bytes:
        synthesis = self.speech.synthesize(
            text=text,
            language=self._language(),
            sample_rate=self.settings.phone_media_sample_rate,
        )
        return wav_to_pcm(b64decode(synthesis.audio_base64))

    def _complete(self, session_id: int) -> None:
        # flush any trailing speech captured before hangup
        tail = self.vad.flush()
        if tail is not None:
            try:
                self._transcribe_and_reply(tail)
            except Exception:
                pass
        complete_voice_session(self.db, session_id=session_id)

    def _language(self) -> str:
        if self.session_id is not None:
            session = get_voice_session(self.db, self.session_id)
            if session is not None:
                return session.language
        return self.settings.default_language

    async def _handle_utterance(self, utterance_pcm: bytes) -> None:
        agent_text = await run_in_threadpool(self._transcribe_and_reply, utterance_pcm)
        if not agent_text:
            return
        await self._speak(agent_text)

    async def _speak(self, text: str) -> None:
        pcm = await run_in_threadpool(self._synthesize_pcm, text)
        # barge-in: clear anything Exotel still has queued before our new utterance
        await self.send({"event": "clear", "stream_sid": self.stream_sid})
        for frame in chunk_frames(pcm):
            await self.send(
                {
                    "event": "media",
                    "stream_sid": self.stream_sid,
                    "media": {"payload": b64encode(frame).decode("ascii")},
                }
            )
