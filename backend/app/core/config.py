from functools import lru_cache
from typing import Annotated, Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Telugu-First AI Voice Agent"
    environment: Literal["development", "test", "production"] = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./ai_voice.db"
    default_language: str = "te-IN"
    # NoDecode: keep pydantic-settings from JSON-decoding this from .env so the
    # comma-separated string form (as in .env.example) is handled by parse_cors_origins.
    cors_origins: Annotated[list[str], NoDecode] = [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:4173",
        "http://localhost:4173",
    ]
    public_base_url: str | None = None
    frontend_base_url: str | None = None

    auth_enabled: bool = True
    admin_username: str = "admin"
    admin_password: str = "admin123"
    auth_secret_key: str = "dev-insecure-change-me"
    access_token_expire_minutes: int = 720
    enquiry_token_expire_minutes: int = 30
    production_require_secure_config: bool = True

    meta_verify_token: str = "change-me"
    meta_access_token: str | None = None
    meta_app_secret: str | None = None
    meta_api_version: str = "v23.0"
    allow_mock_meta_leads: bool = True

    auto_dispatch_calls: bool = True
    telephony_provider: Literal["mock", "exotel"] = "mock"

    exotel_api_key: str | None = None
    exotel_api_token: str | None = None
    exotel_account_sid: str | None = None
    exotel_caller_id: str | None = None
    exotel_from_number: str | None = None
    exotel_region: Literal["in", "sg"] = "in"
    exotel_status_callback_url: str | None = None
    exotel_stream_url: str | None = None
    exotel_flow_url: str | None = None
    # Shared secret in the StreamUrl query so the public media WebSocket only accepts Exotel.
    exotel_stream_secret: str | None = None

    # Phone (Exotel media-stream) audio + VAD tuning.
    phone_media_sample_rate: int = 8000
    phone_vad_silence_ms: int = 700
    phone_vad_energy_threshold: float = 500.0

    sarvam_api_key: str | None = None
    sarvam_stt_ws_url: str = "wss://api.sarvam.ai/speech-to-text/ws"
    sarvam_stt_url: str = "https://api.sarvam.ai/speech-to-text"
    sarvam_tts_url: str = "https://api.sarvam.ai/text-to-speech"
    sarvam_stt_model: str = "saaras:v3"
    sarvam_tts_model: str = "bulbul:v3"
    sarvam_speaker: str = "anushka"

    llm_provider: Literal["mock", "openai_compatible"] = "mock"
    llm_base_url: str | None = None
    llm_api_key: str | None = None
    llm_model: str = "mock-telugu-qualifier"
    # Optional OpenRouter ranking headers; ignored by other OpenAI-compatible endpoints.
    llm_referer: str | None = None
    llm_title: str | None = None

    crm_provider: Literal["mock", "webhook"] = "mock"
    crm_webhook_url: str | None = None
    handoff_channel: Literal["mock", "webhook"] = "mock"
    handoff_webhook_url: str | None = None
    operator_destination: str = "local-operator"

    max_retry_attempts_per_lead: int = 2

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.environment != "production" or not self.production_require_secure_config:
            return self

        insecure_values = []
        if not self.auth_enabled:
            insecure_values.append("AUTH_ENABLED must stay enabled")
        if _is_insecure_secret(self.admin_password):
            insecure_values.append("ADMIN_PASSWORD must be changed")
        if _is_insecure_secret(self.auth_secret_key):
            insecure_values.append("AUTH_SECRET_KEY must be changed")
        if _is_insecure_secret(self.meta_verify_token):
            insecure_values.append("META_VERIFY_TOKEN must be changed")
        if self.allow_mock_meta_leads:
            insecure_values.append("ALLOW_MOCK_META_LEADS must be false")
        if self.telephony_provider == "mock":
            insecure_values.append("TELEPHONY_PROVIDER must not be mock")

        if insecure_values:
            raise ValueError(
                "Production configuration is not secure: " + "; ".join(insecure_values)
            )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def _is_insecure_secret(value: str) -> bool:
    normalized = value.strip().lower()
    return (
        normalized in {"", "admin123", "password", "change-me", "dev-insecure-change-me"}
        or normalized.startswith("replace-with")
        or normalized.endswith(".example.com")
    )
