from app.core.config import Settings
from app.providers.speech.base import SpeechProvider
from app.providers.speech.mock import MockSpeechProvider
from app.providers.speech.sarvam import SarvamSpeechProvider


def build_speech_provider(settings: Settings, provider_name: str | None = None) -> SpeechProvider:
    provider = provider_name or ("sarvam" if settings.sarvam_api_key else "mock")
    if provider == "sarvam":
        return SarvamSpeechProvider(settings)
    return MockSpeechProvider()

