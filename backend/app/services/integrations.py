from app.core.config import Settings, _is_insecure_secret
from app.schemas.voice import IntegrationReadiness


def build_integration_readiness(settings: Settings) -> IntegrationReadiness:
    checks = {
        "auth": _auth_ready(settings),
        "meta": bool(settings.meta_access_token) or settings.allow_mock_meta_leads,
        "telephony": settings.telephony_provider == "mock"
        or all(
            [
                settings.exotel_api_key,
                settings.exotel_api_token,
                settings.exotel_account_sid,
                settings.exotel_caller_id,
                settings.exotel_from_number,
            ]
        ),
        "sarvam": bool(settings.sarvam_api_key) or settings.environment != "production",
        "llm": settings.llm_provider == "mock"
        or bool(settings.llm_base_url and settings.llm_api_key),
        "crm": settings.crm_provider == "mock" or bool(settings.crm_webhook_url),
        "handoff": settings.handoff_channel == "mock" or bool(settings.handoff_webhook_url),
    }
    missing = [key for key, ready in checks.items() if not ready]
    return IntegrationReadiness(**checks, missing=missing)


def _auth_ready(settings: Settings) -> bool:
    if not settings.auth_enabled:
        return settings.environment != "production"
    if settings.environment != "production":
        return True
    return not _is_insecure_secret(settings.admin_password) and not _is_insecure_secret(
        settings.auth_secret_key
    )
