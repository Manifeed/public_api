from __future__ import annotations

from app.clients.networking.user_service_networking_client import get_required_user_service_client

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


def read_account_me(*, session_token: str) -> AccountMeRead:
    return get_required_user_service_client().read_account_me(session_token=session_token)


def update_account_profile(
    *,
    session_token: str,
    payload: AccountProfileUpdateRequestSchema,
) -> AccountProfileUpdateRead:
    return get_required_user_service_client().update_account_profile(
        session_token=session_token,
        payload=payload,
    )


def update_account_password(
    *,
    session_token: str,
    payload: AccountPasswordUpdateRequestSchema,
) -> AccountPasswordUpdateRead:
    return get_required_user_service_client().update_account_password(
        session_token=session_token,
        payload=payload,
    )


def read_account_api_keys(*, session_token: str) -> UserApiKeyListRead:
    return get_required_user_service_client().read_account_api_keys(session_token=session_token)


def create_account_api_key(
    *,
    session_token: str,
    payload: UserApiKeyCreateRequestSchema,
) -> UserApiKeyCreateRead:
    return get_required_user_service_client().create_account_api_key(
        session_token=session_token,
        payload=payload,
    )


def delete_account_api_key(
    *,
    session_token: str,
    api_key_id: int,
) -> UserApiKeyDeleteRead:
    return get_required_user_service_client().delete_account_api_key(
        session_token=session_token,
        api_key_id=api_key_id,
    )
