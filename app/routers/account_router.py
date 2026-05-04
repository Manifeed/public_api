from fastapi import APIRouter, Depends, Path, Request, Response

from app.dependencies.auth_dependencies import (
    require_authenticated_user,
    require_masked_api_enabled_user,
)
from app.middleware.rate_limit import enforce_rate_limit
from app.services import account_service
from app.utils.session_cookie import clear_session_cookie, get_session_token_from_request

from shared_backend.schemas.account.account_schema import (
    AccountMeRead,
    AccountPasswordUpdateRead,
    AccountPasswordUpdateRequestSchema,
    AccountProfileUpdateRead,
    AccountProfileUpdateRequestSchema,
    UserApiKeyCreateRead,
    UserApiKeyCreateRequestSchema,
    UserApiKeyDeleteRead,
    UserApiKeyListRead,
)

account_router = APIRouter(prefix="/api/account", tags=["account"])


@account_router.get("/me", response_model=AccountMeRead)
def read_account_me_route(
    request: Request,
    _current_user=Depends(require_authenticated_user),
) -> AccountMeRead:
    return account_service.read_account_me(
        session_token=get_session_token_from_request(request) or "",
    )


@account_router.patch("/me", response_model=AccountProfileUpdateRead)
def update_account_me_route(
    request: Request,
    payload: AccountProfileUpdateRequestSchema,
    _current_user=Depends(require_authenticated_user),
) -> AccountProfileUpdateRead:
    return account_service.update_account_profile(
        session_token=get_session_token_from_request(request) or "",
        payload=payload,
    )


@account_router.patch("/password", response_model=AccountPasswordUpdateRead)
def update_account_password_route(
    request: Request,
    payload: AccountPasswordUpdateRequestSchema,
    response: Response,
    current_user=Depends(require_authenticated_user),
) -> AccountPasswordUpdateRead:
    enforce_rate_limit(
        namespace="account-password-user",
        identifier=str(current_user.user_id),
        limit=5,
        window_seconds=3600,
    )
    result = account_service.update_account_password(
        session_token=get_session_token_from_request(request) or "",
        payload=payload,
    )
    clear_session_cookie(response)
    return result


@account_router.get("/api-keys", response_model=UserApiKeyListRead)
def read_account_api_keys_route(
    request: Request,
    _current_user=Depends(require_masked_api_enabled_user),
) -> UserApiKeyListRead:
    return account_service.read_account_api_keys(
        session_token=get_session_token_from_request(request) or "",
    )


@account_router.post("/api-keys", response_model=UserApiKeyCreateRead)
def create_account_api_key_route(
    request: Request,
    payload: UserApiKeyCreateRequestSchema,
    current_user=Depends(require_masked_api_enabled_user),
) -> UserApiKeyCreateRead:
    enforce_rate_limit(
        namespace="account-api-key-create-user",
        identifier=str(current_user.user_id),
        limit=5,
        window_seconds=3600,
    )
    return account_service.create_account_api_key(
        session_token=get_session_token_from_request(request) or "",
        payload=payload,
    )


@account_router.delete("/api-keys/{api_key_id}", response_model=UserApiKeyDeleteRead)
def delete_account_api_key_route(
    request: Request,
    api_key_id: int = Path(ge=1),
    _current_user=Depends(require_masked_api_enabled_user),
) -> UserApiKeyDeleteRead:
    return account_service.delete_account_api_key(
        session_token=get_session_token_from_request(request) or "",
        api_key_id=api_key_id,
    )
