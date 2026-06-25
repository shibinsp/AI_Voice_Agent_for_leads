from app.core.config import Settings
from app.providers.telephony.base import TelephonyProvider
from app.providers.telephony.exotel import ExotelProvider
from app.providers.telephony.mock import MockTelephonyProvider


def build_telephony_provider(settings: Settings) -> TelephonyProvider:
    if settings.telephony_provider == "exotel":
        return ExotelProvider(settings)
    return MockTelephonyProvider()

