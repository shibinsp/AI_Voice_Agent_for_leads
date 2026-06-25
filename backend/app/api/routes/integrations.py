from fastapi import APIRouter, Depends

from app.api.deps import get_app_settings
from app.core.config import Settings
from app.schemas.voice import IntegrationReadiness
from app.services.integrations import build_integration_readiness

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/readiness", response_model=IntegrationReadiness)
def get_readiness(settings: Settings = Depends(get_app_settings)) -> IntegrationReadiness:
    return build_integration_readiness(settings)
