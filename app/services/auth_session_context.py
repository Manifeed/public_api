from __future__ import annotations

from datetime import datetime, timezone
import os

from app.clients.networking.auth_service_networking_client import get_required_auth_service_client
from app.clients.networking.redis_networking_client import RedisCommandError, RedisNetworkingClient

from shared_backend.domain.current_user import (
    AuthenticatedUserContext,
    authenticated_user_context_from_resolved_session,
)
from shared_backend.utils.auth_utils import hash_secret_token

DEFAULT_AUTH_CONTEXT_CACHE_TTL_SECONDS = 45


def resolve_authenticated_user(*, session_token: str) -> AuthenticatedUserContext:
    cached_context = _read_cached_auth_context(session_token=session_token)
    if cached_context is not None:
        return cached_context

    resolved_session = get_required_auth_service_client().resolve_session(session_token=session_token)
    context = authenticated_user_context_from_resolved_session(resolved_session)
    _write_cached_auth_context(session_token=session_token, current_user=context)
    return context


def invalidate_auth_context_cache(*, session_token: str) -> None:
    if not session_token:
        return
    try:
        RedisNetworkingClient().delete_key(_build_auth_context_cache_key(session_token=session_token))
    except RedisCommandError:
        return


def _read_cached_auth_context(*, session_token: str) -> AuthenticatedUserContext | None:
    if not session_token:
        return None
    try:
        payload = RedisNetworkingClient().get_json(_build_auth_context_cache_key(session_token=session_token))
    except RedisCommandError:
        return None
    if payload is None:
        return None
    try:
        session_expires_at = datetime.fromisoformat(str(payload["session_expires_at"]))
    except (KeyError, TypeError, ValueError):
        invalidate_auth_context_cache(session_token=session_token)
        return None
    if session_expires_at <= datetime.now(timezone.utc):
        invalidate_auth_context_cache(session_token=session_token)
        return None
    try:
        return AuthenticatedUserContext(
            user_id=int(payload["user_id"]),
            email=str(payload["email"]),
            role=str(payload["role"]),
            is_active=bool(payload["is_active"]),
            api_access_enabled=bool(payload["api_access_enabled"]),
            session_expires_at=session_expires_at,
        )
    except (KeyError, TypeError, ValueError):
        invalidate_auth_context_cache(session_token=session_token)
        return None


def _write_cached_auth_context(*, session_token: str, current_user: AuthenticatedUserContext) -> None:
    remaining_seconds = int(
        max(
            0,
            (current_user.session_expires_at - datetime.now(timezone.utc)).total_seconds(),
        )
    )
    if remaining_seconds <= 0:
        return
    ttl_seconds = min(_resolve_auth_context_cache_ttl_seconds(), remaining_seconds)
    if ttl_seconds <= 0:
        return
    try:
        RedisNetworkingClient().set_json_with_ttl(
            _build_auth_context_cache_key(session_token=session_token),
            {
                "user_id": current_user.user_id,
                "email": current_user.email,
                "role": current_user.role,
                "is_active": current_user.is_active,
                "api_access_enabled": current_user.api_access_enabled,
                "session_expires_at": current_user.session_expires_at.isoformat(),
            },
            ttl_seconds,
        )
    except RedisCommandError:
        return


def _build_auth_context_cache_key(*, session_token: str) -> str:
    return f"manifeed:auth-context:{hash_secret_token(session_token)}"


def _resolve_auth_context_cache_ttl_seconds() -> int:
    raw_value = os.getenv("AUTH_CONTEXT_CACHE_TTL_SECONDS", str(DEFAULT_AUTH_CONTEXT_CACHE_TTL_SECONDS)).strip()
    try:
        parsed = int(raw_value)
    except ValueError:
        return DEFAULT_AUTH_CONTEXT_CACHE_TTL_SECONDS
    if parsed <= 0:
        return DEFAULT_AUTH_CONTEXT_CACHE_TTL_SECONDS
    return parsed
