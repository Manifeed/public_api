from __future__ import annotations

from fastapi import Depends, Request

from shared_backend.errors.app_error import NotFoundError
from shared_backend.errors.custom_exceptions import (
    AdminAccessRequiredError,
    ApiAccessDisabledError,
    MissingSessionTokenError,
)
from app.services.auth_service import resolve_authenticated_user
from app.utils.session_cookie import get_session_token_from_request

from shared_backend.domain.current_user import AuthenticatedUserContext


def require_authenticated_user(request: Request) -> AuthenticatedUserContext:
    session_token = get_session_token_from_request(request)
    if not session_token:
        raise MissingSessionTokenError()
    return resolve_authenticated_user(session_token=session_token)


def require_admin_user(
    current_user: AuthenticatedUserContext = Depends(require_authenticated_user),
) -> AuthenticatedUserContext:
    if current_user.role != "admin":
        raise AdminAccessRequiredError()
    return current_user


def require_api_enabled_user(
    current_user: AuthenticatedUserContext = Depends(require_authenticated_user),
) -> AuthenticatedUserContext:
    if not current_user.api_access_enabled:
        raise ApiAccessDisabledError()
    return current_user


def require_masked_admin_user(
    current_user: AuthenticatedUserContext = Depends(require_authenticated_user),
) -> AuthenticatedUserContext:
    if current_user.role != "admin":
        raise NotFoundError()
    return current_user


def require_masked_api_enabled_user(
    current_user: AuthenticatedUserContext = Depends(require_authenticated_user),
) -> AuthenticatedUserContext:
    if not current_user.api_access_enabled:
        raise NotFoundError()
    return current_user
