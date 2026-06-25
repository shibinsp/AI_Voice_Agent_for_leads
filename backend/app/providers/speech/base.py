from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class SpeechSynthesisResult:
    audio_base64: str
    mime_type: str
    provider_payload: dict


@dataclass(slots=True)
class TranscriptionResult:
    text: str
    language: str | None
    confidence: float | None
    provider_payload: dict


class SpeechProvider(ABC):
    name: str

    @abstractmethod
    def synthesize(
        self,
        *,
        text: str,
        language: str,
        sample_rate: int | None = None,
    ) -> SpeechSynthesisResult:
        raise NotImplementedError

    @abstractmethod
    def transcribe(
        self,
        *,
        audio_base64: str,
        mime_type: str,
        language: str,
    ) -> TranscriptionResult:
        raise NotImplementedError
