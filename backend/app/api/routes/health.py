from fastapi import APIRouter, Depends

from app.api.deps import get_app_settings
from app.core.config import Settings

router = APIRouter(tags=["health"])


@router.get("/health")
def healthcheck(settings: Settings = Depends(get_app_settings)) -> dict[str, str]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
    }

