from app.core.config import Settings
from app.providers.crm.base import CrmProvider
from app.providers.crm.mock import MockCrmProvider
from app.providers.crm.webhook import WebhookCrmProvider


def build_crm_provider(settings: Settings) -> CrmProvider:
    if settings.crm_provider == "webhook":
        return WebhookCrmProvider(settings)
    return MockCrmProvider()
