from collections.abc import Generator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_session_factory
from app.providers.telephony.base import TelephonyProvider
from app.providers.telephony.factory import build_telephony_provider
from app.schemas.auth import CurrentUser
from app.services.auth import AuthError, verify_access_token
from app.services.meta import MetaLeadClient


def get_db() -> Generator[Session, None, None]:
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


def get_meta_lead_client() -> MetaLeadClient:
    return MetaLeadClient(get_settings())


def get_telephony_provider() -> TelephonyProvider:
    return build_telephony_provider(get_settings())


def get_app_settings() -> Settings:
    return get_settings()


def get_current_user(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_app_settings),
) -> CurrentUser:
    if not settings.auth_enabled:
        return CurrentUser(username="local-dev")

    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        username = verify_access_token(settings, token)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return CurrentUser(username=username)
