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
from shared_backend.domain.current_user import AuthenticatedUserContext


def register_auth_user(payload: AuthRegisterRequestSchema) -> AuthRegisterRead:
    return get_required_auth_service_client().register(payload)


def login_auth_user(payload: AuthLoginRequestSchema) -> AuthLoginResult:
    return get_required_auth_service_client().login(payload)


def read_auth_session(*, session_token: str) -> AuthSessionRead:
    return get_required_auth_service_client().read_session(session_token=session_token)


def logout_auth_user(*, session_token: str) -> AuthLogoutRead:
    return get_required_auth_service_client().logout(session_token=session_token)


def resolve_authenticated_user(*, session_token: str) -> AuthenticatedUserContext:
    resolved_session = get_required_auth_service_client().resolve_session(session_token=session_token)
    return AuthenticatedUserContext(
        user_id=resolved_session.user_id,
        email=resolved_session.email,
        role=resolved_session.role,
        is_active=resolved_session.is_active,
        api_access_enabled=resolved_session.api_access_enabled,
        session_expires_at=resolved_session.session_expires_at,
    )
