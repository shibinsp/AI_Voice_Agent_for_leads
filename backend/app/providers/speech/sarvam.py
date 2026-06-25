from __future__ import annotations

import mimetypes
from base64 import b64decode

import httpx

from app.core.config import Settings
from app.providers.speech.base import (
    SpeechProvider,
    SpeechSynthesisResult,
    TranscriptionResult,
)


class SarvamSpeechProvider(SpeechProvider):
    name = "sarvam"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def synthesize(
        self,
        *,
        text: str,
        language: str,
        sample_rate: int | None = None,
    ) -> SpeechSynthesisResult:
        if not self.settings.sarvam_api_key:
            raise RuntimeError("SARVAM_API_KEY is required for Sarvam speech synthesis")

        payload: dict = {
            "text": text,
            "target_language_code": language,
            "speaker": self.settings.sarvam_speaker,
            "model": self.settings.sarvam_tts_model,
            "audio_format": "wav",
        }
        if sample_rate:
            # Match phone audio (8 kHz) so frames can be streamed straight back to Exotel.
            payload["speech_sample_rate"] = sample_rate
        headers = {"api-subscription-key": self.settings.sarvam_api_key}
        with httpx.Client(timeout=20) as client:
            response = client.post(self.settings.sarvam_tts_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        audios = data.get("audios") or []
        if not audios:
            raise RuntimeError("Sarvam TTS response did not include audio")
        return SpeechSynthesisResult(
            audio_base64=audios[0],
            mime_type="audio/wav",
            provider_payload=data,
        )

    def transcribe(
        self,
        *,
        audio_base64: str,
        mime_type: str,
        language: str,
    ) -> TranscriptionResult:
        if not self.settings.sarvam_api_key:
            raise RuntimeError("SARVAM_API_KEY is required for Sarvam transcription")

        audio_bytes = b64decode(audio_base64)
        extension = mimetypes.guess_extension(mime_type) or ".wav"
        files = {"file": (f"utterance{extension}", audio_bytes, mime_type or "audio/wav")}
        # The saaras model auto-detects Indic languages and tolerates Telugu-English code-mix.
        data = {"model": self.settings.sarvam_stt_model, "language_code": language}
        headers = {"api-subscription-key": self.settings.sarvam_api_key}
        with httpx.Client(timeout=30) as client:
            response = client.post(
                self.settings.sarvam_stt_url,
                files=files,
                data=data,
                headers=headers,
            )
        response.raise_for_status()
        payload = response.json()
        text = (payload.get("transcript") or "").strip()
        return TranscriptionResult(
            text=text,
            language=payload.get("language_code") or language,
            confidence=None,
            provider_payload=payload,
        )
