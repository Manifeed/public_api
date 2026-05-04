from __future__ import annotations

from app.clients.networking.auth_service_networking_client import get_required_auth_service_client

from shared_backend.schemas.auth.auth_schema import (
    AuthLoginRequestSchema,
    AuthLogoutRead,
    AuthRegisterRead,
    AuthRegisterRequestSchema,
    AuthSessionRead,
)
from shared_backend.schemas.auth.session_schema import AuthLoginResult


def register_auth_user(payload: AuthRegisterRequestSchema) -> AuthRegisterRead:
    return get_required_auth_service_client().register(payload)


def login_auth_user(payload: AuthLoginRequestSchema) -> AuthLoginResult:
    return get_required_auth_service_client().login(payload)


def read_auth_session(*, session_token: str) -> AuthSessionRead:
    return get_required_auth_service_client().read_session(session_token=session_token)


def logout_auth_user(*, session_token: str) -> AuthLogoutRead:
    from app.services.auth_session_context import invalidate_auth_context_cache

    result = get_required_auth_service_client().logout(session_token=session_token)
    invalidate_auth_context_cache(session_token=session_token)
    return result
