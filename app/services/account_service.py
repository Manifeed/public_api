from __future__ import annotations

from app.clients.networking.user_service_networking_client import get_required_user_service_client

from shared_backend.domain.current_user import AuthenticatedUserContext
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


def read_account_me(*, current_user: AuthenticatedUserContext) -> AccountMeRead:
    return get_required_user_service_client().read_account_me(current_user=current_user)


def update_account_profile(
    *,
        current_user: AuthenticatedUserContext,
        payload: AccountProfileUpdateRequestSchema,
) -> AccountProfileUpdateRead:
    return get_required_user_service_client().update_account_profile(
        current_user=current_user,
        payload=payload,
    )


def update_account_password(
    *,
        current_user: AuthenticatedUserContext,
        payload: AccountPasswordUpdateRequestSchema,
) -> AccountPasswordUpdateRead:
    return get_required_user_service_client().update_account_password(
        current_user=current_user,
        payload=payload,
    )


def read_account_api_keys(*, current_user: AuthenticatedUserContext) -> UserApiKeyListRead:
    return get_required_user_service_client().read_account_api_keys(current_user=current_user)


def create_account_api_key(
    *,
        current_user: AuthenticatedUserContext,
        payload: UserApiKeyCreateRequestSchema,
) -> UserApiKeyCreateRead:
    return get_required_user_service_client().create_account_api_key(
        current_user=current_user,
        payload=payload,
    )


def delete_account_api_key(
    *,
        current_user: AuthenticatedUserContext,
        api_key_id: int,
) -> UserApiKeyDeleteRead:
    return get_required_user_service_client().delete_account_api_key(
        current_user=current_user,
        api_key_id=api_key_id,
    )
