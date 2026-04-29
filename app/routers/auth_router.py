from fastapi import APIRouter, Depends, Request, Response

from app.dependencies.auth_dependencies import require_authenticated_user
from app.middleware.rate_limit import enforce_rate_limit
from app.schemas.auth.auth_schema import (
    AuthLoginRead,
    AuthLoginRequestSchema,
    AuthLogoutRead,
    AuthRegisterRead,
    AuthRegisterRequestSchema,
    AuthSessionRead,
)
from app.services import auth_service
from app.utils.session_cookie import (
    clear_session_cookie,
    get_session_token_from_request,
    set_session_cookie,
)


auth_router = APIRouter(prefix="/api/auth", tags=["auth"])


@auth_router.post("/register", response_model=AuthRegisterRead)
def register_auth_user(
    request: Request,
    payload: AuthRegisterRequestSchema,
) -> AuthRegisterRead:
    enforce_rate_limit(
        request,
        namespace="auth-register-ip",
        limit=10,
        window_seconds=3600,
    )
    return auth_service.register_auth_user(payload)


@auth_router.post("/login", response_model=AuthLoginRead)
def login_auth_user(
    request: Request,
    payload: AuthLoginRequestSchema,
    response: Response,
) -> AuthLoginRead:
    enforce_rate_limit(
        request,
        namespace="auth-login-ip",
        limit=30,
        window_seconds=300,
    )
    enforce_rate_limit(
        request,
        namespace="auth-login-email",
        identifier=payload.email.strip().lower(),
        limit=10,
        window_seconds=300,
    )
    result = auth_service.login_auth_user(payload)
    set_session_cookie(
        response,
        session_token=result.session_token,
        expires_at=result.expires_at,
    )
    return AuthLoginRead(
        expires_at=result.expires_at,
        user=result.user,
    )


@auth_router.post("/logout", response_model=AuthLogoutRead)
def logout_auth_user(
    request: Request,
    response: Response,
    _current_user=Depends(require_authenticated_user),
) -> AuthLogoutRead:
    result = auth_service.logout_auth_user(
        session_token=get_session_token_from_request(request) or "",
    )
    clear_session_cookie(response)
    return result


@auth_router.get("/session", response_model=AuthSessionRead)
def read_auth_session(
    request: Request,
    _current_user=Depends(require_authenticated_user),
) -> AuthSessionRead:
    return auth_service.read_auth_session(
        session_token=get_session_token_from_request(request) or "",
    )
