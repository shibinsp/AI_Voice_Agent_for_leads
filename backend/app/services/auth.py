from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any

from app.core.config import Settings


class AuthError(ValueError):
    pass


def verify_credentials(settings: Settings, username: str, password: str) -> bool:
    username_ok = secrets.compare_digest(username, settings.admin_username)
    password_ok = secrets.compare_digest(password, settings.admin_password)
    return username_ok and password_ok


def create_access_token(
    settings: Settings,
    subject: str,
    expires_in_minutes: int | None = None,
) -> tuple[str, int]:
    minutes = expires_in_minutes if expires_in_minutes is not None else settings.access_token_expire_minutes
    expires_in = minutes * 60
    now = int(time.time())
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + expires_in,
    }
    header = {
        "alg": "HS256",
        "typ": "JWT",
    }
    signing_input = ".".join(
        [
            _base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8")),
            _base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")),
        ]
    )
    signature = _sign(settings.auth_secret_key, signing_input)
    return f"{signing_input}.{signature}", expires_in


def verify_access_token(settings: Settings, token: str) -> str:
    try:
        header_segment, payload_segment, signature = token.split(".", 2)
    except ValueError as exc:
        raise AuthError("Invalid token format") from exc

    signing_input = f"{header_segment}.{payload_segment}"
    expected_signature = _sign(settings.auth_secret_key, signing_input)
    if not hmac.compare_digest(signature, expected_signature):
        raise AuthError("Invalid token signature")

    try:
        header = json.loads(_base64url_decode(header_segment))
        payload: dict[str, Any] = json.loads(_base64url_decode(payload_segment))
    except (ValueError, json.JSONDecodeError) as exc:
        raise AuthError("Invalid token payload") from exc

    if header.get("alg") != "HS256":
        raise AuthError("Unsupported token algorithm")

    subject = payload.get("sub")
    expires_at = payload.get("exp")
    if not isinstance(subject, str) or not subject:
        raise AuthError("Missing token subject")
    if not isinstance(expires_at, int) or expires_at < int(time.time()):
        raise AuthError("Token expired")

    return subject


def _sign(secret: str, signing_input: str) -> str:
    digest = hmac.new(
        secret.encode("utf-8"),
        signing_input.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return _base64url_encode(digest)


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64url_decode(value: str) -> str:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}").decode("utf-8")
