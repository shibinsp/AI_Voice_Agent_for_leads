from __future__ import annotations

import struct
from base64 import b64encode

from app.providers.speech.base import (
    SpeechProvider,
    SpeechSynthesisResult,
    TranscriptionResult,
)

# A canned Telugu/English code-mix utterance so the live loop is fully exercisable
# without Sarvam credentials. Mirrors the kind of input the brief expects from Hyderabad leads.
_MOCK_LEAD_UTTERANCE = "Haan, naaku interest undi. Appointment book cheyandi today please."


def _silent_wav(*, duration_ms: int = 200, sample_rate: int = 8000) -> bytes:
    """Build a minimal valid mono 16-bit PCM WAV of silence.

    Phone audio is 8 kHz narrowband (brief §4.2), so we emit at 8 kHz. The point is a
    byte-valid WAV the browser ``<audio>`` element can load without erroring in mock mode.
    """
    num_samples = int(sample_rate * duration_ms / 1000)
    data = b"\x00\x00" * num_samples
    block_align = 2
    byte_rate = sample_rate * block_align
    header = b"RIFF" + struct.pack("<I", 36 + len(data)) + b"WAVE"
    header += b"fmt " + struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, byte_rate, block_align, 16)
    header += b"data" + struct.pack("<I", len(data))
    return header + data


class MockSpeechProvider(SpeechProvider):
    name = "mock"

    def synthesize(
        self,
        *,
        text: str,
        language: str,
        sample_rate: int | None = None,
    ) -> SpeechSynthesisResult:
        return SpeechSynthesisResult(
            audio_base64=b64encode(_silent_wav(sample_rate=sample_rate or 8000)).decode("ascii"),
            mime_type="audio/wav",
            provider_payload={"mock": True, "language": language, "text": text},
        )

    def transcribe(
        self,
        *,
        audio_base64: str,
        mime_type: str,
        language: str,
    ) -> TranscriptionResult:
        return TranscriptionResult(
            text=_MOCK_LEAD_UTTERANCE,
            language=language,
            confidence=0.9,
            provider_payload={"mock": True, "input_bytes": len(audio_base64)},
        )
