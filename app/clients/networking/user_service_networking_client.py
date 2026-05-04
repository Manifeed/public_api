from __future__ import annotations

from typing import Any

import httpx

from app.clients.networking.service_client_registry import get_service_http_client_registry
from app.clients.networking.service_http_client import (
    ServiceClientConfig,
    build_service_config,
    request_service,
    require_service_client,
)
from shared_backend.schemas.internal.service_schema import InternalServiceHealthRead

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
from shared_backend.schemas.internal.user_service_schema import (
    InternalAccountPasswordUpdateRequest,
    InternalAccountProfileUpdateRequest,
    InternalApiKeyCreateRequest,
)
from shared_backend.schemas.internal.auth_service_schema import InternalSessionTokenRequest


class UserServiceNetworkingClient:
    def __init__(
        self,
        config: ServiceClientConfig,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._config = config
        self._http_client = http_client

    @classmethod
    def from_env(cls) -> "UserServiceNetworkingClient | None":
        config = build_service_config(
            base_url_env="USER_SERVICE_URL",
            timeout_env="USER_SERVICE_TIMEOUT_SECONDS",
            default_timeout_seconds=5.0,
            service_name="User",
        )
        if config is None:
            return None
        registry = get_service_http_client_registry()
        return cls(config, http_client=registry.user if registry is not None else None)

    def read_account_me(self, *, session_token: str) -> AccountMeRead:
        response = self._post(
            "/internal/users/account/me",
            json={"payload": InternalSessionTokenRequest(session_token=session_token).model_dump(mode="json")},
        )
        return AccountMeRead.model_validate(response.json())

    def update_account_profile(
        self,
        *,
        session_token: str,
        payload: AccountProfileUpdateRequestSchema,
    ) -> AccountProfileUpdateRead:
        response = self._patch(
            "/internal/users/account/me",
            json={
                "payload": InternalAccountProfileUpdateRequest(
                    session_token=session_token,
                    payload=payload,
                ).model_dump(mode="json", exclude_none=True)
            },
        )
        return AccountProfileUpdateRead.model_validate(response.json())

    def update_account_password(
        self,
        *,
        session_token: str,
        payload: AccountPasswordUpdateRequestSchema,
    ) -> AccountPasswordUpdateRead:
        response = self._patch(
            "/internal/users/account/password",
            json={
                "payload": InternalAccountPasswordUpdateRequest(
                    session_token=session_token,
                    payload=payload,
                ).model_dump(mode="json")
            },
        )
        return AccountPasswordUpdateRead.model_validate(response.json())

    def read_account_api_keys(self, *, session_token: str) -> UserApiKeyListRead:
        response = self._post(
            "/internal/users/account/api-keys/list",
            json={"payload": InternalSessionTokenRequest(session_token=session_token).model_dump(mode="json")},
        )
        return UserApiKeyListRead.model_validate(response.json())

    def create_account_api_key(
        self,
        *,
        session_token: str,
        payload: UserApiKeyCreateRequestSchema,
    ) -> UserApiKeyCreateRead:
        response = self._post(
            "/internal/users/account/api-keys",
            json={
                "payload": InternalApiKeyCreateRequest(
                    session_token=session_token,
                    payload=payload,
                ).model_dump(mode="json")
            },
        )
        return UserApiKeyCreateRead.model_validate(response.json())

    def delete_account_api_key(
        self,
        *,
        session_token: str,
        api_key_id: int,
    ) -> UserApiKeyDeleteRead:
        response = self._post(
            f"/internal/users/account/api-keys/{api_key_id}/delete",
            json={"payload": InternalSessionTokenRequest(session_token=session_token).model_dump(mode="json")},
        )
        return UserApiKeyDeleteRead.model_validate(response.json())

    def _get(self, path: str, *, params: dict[str, Any]) -> httpx.Response:
        return self._request("GET", path, params=params, json=None)

    def _post(self, path: str, *, json: dict[str, Any]) -> httpx.Response:
        return self._request("POST", path, params=None, json=json)

    def _patch(self, path: str, *, json: dict[str, Any]) -> httpx.Response:
        return self._request("PATCH", path, params=None, json=json)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None,
        json: dict[str, Any] | None,
    ) -> httpx.Response:
        return request_service(
            config=self._config,
            method=method,
            path=path,
            params=params,
            json=json,
            http_client=self._http_client,
        )

    def read_internal_health(self) -> InternalServiceHealthRead:
        response = self._request("GET", "/internal/health", params=None, json=None)
        return InternalServiceHealthRead.model_validate(response.json())


def get_user_service_client() -> UserServiceNetworkingClient | None:
    return UserServiceNetworkingClient.from_env()


def get_required_user_service_client() -> UserServiceNetworkingClient:
    return require_service_client(
        get_user_service_client(),
        env_name="USER_SERVICE_URL",
    )
