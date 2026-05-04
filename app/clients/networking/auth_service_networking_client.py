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
from shared_backend.schemas.internal.service_schema import InternalResolvedSessionRead, InternalServiceHealthRead

from shared_backend.schemas.auth.auth_schema import (
    AuthLoginRequestSchema,
    AuthLogoutRead,
    AuthRegisterRead,
    AuthRegisterRequestSchema,
    AuthSessionRead,
)
from shared_backend.schemas.auth.session_schema import AuthLoginResult
from shared_backend.schemas.internal.auth_service_schema import InternalAuthLoginRead, InternalSessionTokenRequest


class AuthServiceNetworkingClient:
    def __init__(
        self,
        config: ServiceClientConfig,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._config = config
        self._http_client = http_client

    @classmethod
    def from_env(cls) -> "AuthServiceNetworkingClient | None":
        config = build_service_config(
            base_url_env="AUTH_SERVICE_URL",
            timeout_env="AUTH_SERVICE_TIMEOUT_SECONDS",
            default_timeout_seconds=5.0,
            service_name="Auth",
        )
        if config is None:
            return None
        registry = get_service_http_client_registry()
        return cls(config, http_client=registry.auth if registry is not None else None)

    def register(self, payload: AuthRegisterRequestSchema) -> AuthRegisterRead:
        response = self._post(
            "/internal/auth/register",
            json={"payload": payload.model_dump(mode="json")},
        )
        return AuthRegisterRead.model_validate(response.json())

    def login(self, payload: AuthLoginRequestSchema) -> AuthLoginResult:
        response = self._post(
            "/internal/auth/login",
            json={"payload": payload.model_dump(mode="json")},
        )
        result = InternalAuthLoginRead.model_validate(response.json())
        return AuthLoginResult(
            session_token=result.session_token,
            expires_at=result.expires_at,
            user=result.user,
        )

    def read_session(self, *, session_token: str) -> AuthSessionRead:
        response = self._post(
            "/internal/auth/session",
            json={"payload": InternalSessionTokenRequest(session_token=session_token).model_dump(mode="json")},
        )
        return AuthSessionRead.model_validate(response.json())

    def resolve_session(self, *, session_token: str) -> InternalResolvedSessionRead:
        response = self._post(
            "/internal/auth/resolve-session",
            json={"payload": InternalSessionTokenRequest(session_token=session_token).model_dump(mode="json")},
        )
        return InternalResolvedSessionRead.model_validate(response.json())

    def logout(self, *, session_token: str) -> AuthLogoutRead:
        response = self._post(
            "/internal/auth/logout",
            json={"payload": InternalSessionTokenRequest(session_token=session_token).model_dump(mode="json")},
        )
        return AuthLogoutRead.model_validate(response.json())

    def read_internal_health(self) -> InternalServiceHealthRead:
        response = request_service(
            config=self._config,
            method="GET",
            path="/internal/health",
            http_client=self._http_client,
        )
        return InternalServiceHealthRead.model_validate(response.json())

    def _post(self, path: str, *, json: dict[str, Any]) -> httpx.Response:
        return request_service(
            config=self._config,
            method="POST",
            path=path,
            json=json,
            http_client=self._http_client,
        )


def get_auth_service_client() -> AuthServiceNetworkingClient | None:
    return AuthServiceNetworkingClient.from_env()


def get_required_auth_service_client() -> AuthServiceNetworkingClient:
    return require_service_client(
        get_auth_service_client(),
        env_name="AUTH_SERVICE_URL",
    )
