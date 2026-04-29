from __future__ import annotations

import os
from datetime import datetime

from fastapi import Request, Response

SESSION_COOKIE_NAME = "manifeed_session"
SESSION_COOKIE_SAMESITE = "lax"


def get_session_token_from_request(request: Request) -> str | None:
    cookie_token = request.cookies.get(SESSION_COOKIE_NAME)
    if cookie_token and cookie_token.strip():
        return cookie_token.strip()
    return None


def set_session_cookie(
    response: Response,
    *,
    session_token: str,
    expires_at: datetime,
) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        httponly=True,
        samesite=SESSION_COOKIE_SAMESITE,
        secure=is_session_cookie_secure(),
        path="/",
        expires=expires_at,
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        samesite=SESSION_COOKIE_SAMESITE,
        secure=is_session_cookie_secure(),
        path="/",
    )


def is_session_cookie_secure() -> bool:
    for env_var in ("AUTH_SESSION_COOKIE_SECURE", "APP_ENV", "ENVIRONMENT", "NODE_ENV"):
        raw_value = os.getenv(env_var)
        if raw_value is None:
            continue
        normalized = raw_value.strip().lower()
        if normalized in {"1", "true", "yes", "on", "prod", "production"}:
            return True
        if normalized in {"0", "false", "no", "off", "dev", "development", "local"}:
            return False
    return True
