from __future__ import annotations

from datetime import datetime

from fastapi import Request, Response

SESSION_COOKIE_NAME = "manifeed_session"
SESSION_COOKIE_SAMESITE = "lax"


def get_session_token_from_request(request: Request) -> str | None:
    cookie_token = request.cookies.get(SESSION_COOKIE_NAME)
    if cookie_token and cookie_token.strip():
        return cookie_token.strip()
    return None


def infer_session_cookie_secure(request: Request) -> bool:
    forwarded_proto = (request.headers.get("x-forwarded-proto") or "").split(",")[0].strip().lower()
    if forwarded_proto == "https":
        return True
    if forwarded_proto == "http":
        return False
    return request.url.scheme == "https"


def set_session_cookie(
    response: Response,
    request: Request,
    *,
    session_token: str,
    expires_at: datetime,
) -> None:
    secure = infer_session_cookie_secure(request)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        httponly=True,
        samesite=SESSION_COOKIE_SAMESITE,
        secure=secure,
        path="/",
        expires=expires_at,
    )


def clear_session_cookie(response: Response, request: Request) -> None:
    secure = infer_session_cookie_secure(request)
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        samesite=SESSION_COOKIE_SAMESITE,
        secure=secure,
        path="/",
    )
