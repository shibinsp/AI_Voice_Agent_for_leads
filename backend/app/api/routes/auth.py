from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_app_settings, get_current_user
from app.core.config import Settings
from app.schemas.auth import CurrentUser, LoginRequest, TokenResponse
from app.services.auth import create_access_token, verify_credentials

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    settings: Settings = Depends(get_app_settings),
) -> TokenResponse:
    if settings.auth_enabled and not verify_credentials(
        settings,
        payload.username,
        payload.password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    subject = payload.username if settings.auth_enabled else "local-dev"
    token, expires_in = create_access_token(settings, subject)
    return TokenResponse(
        access_token=token,
        expires_in=expires_in,
        username=subject,
    )


@router.get("/me", response_model=CurrentUser)
def me(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return current_user
