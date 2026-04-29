from __future__ import annotations

from typing import Any

import httpx

from app.clients.networking.service_http_client import (
    ServiceClientConfig,
    build_service_config,
    request_service,
    require_service_client,
)
from app.schemas.auth.auth_schema import (
    AuthLoginRequestSchema,
    AuthLogoutRead,
    AuthRegisterRead,
    AuthRegisterRequestSchema,
    AuthSessionRead,
)
from app.schemas.auth.session_schema import AuthLoginResult
from app.schemas.internal.auth_service_schema import InternalAuthLoginRead
from app.schemas.internal.service_schema import InternalResolvedSessionRead


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
        return cls(config)

    def register(self, payload: AuthRegisterRequestSchema) -> AuthRegisterRead:
        response = self._post("/internal/auth/register", json=payload.model_dump(mode="json"))
        return AuthRegisterRead.model_validate(response.json())

    def login(self, payload: AuthLoginRequestSchema) -> AuthLoginResult:
        response = self._post("/internal/auth/login", json=payload.model_dump(mode="json"))
        result = InternalAuthLoginRead.model_validate(response.json())
        return AuthLoginResult(
            session_token=result.session_token,
            expires_at=result.expires_at,
            user=result.user,
        )

    def read_session(self, *, session_token: str) -> AuthSessionRead:
        response = self._post("/internal/auth/session", json={"session_token": session_token})
        return AuthSessionRead.model_validate(response.json())

    def resolve_session(self, *, session_token: str) -> InternalResolvedSessionRead:
        response = self._post("/internal/auth/resolve-session", json={"session_token": session_token})
        return InternalResolvedSessionRead.model_validate(response.json())

    def logout(self, *, session_token: str) -> AuthLogoutRead:
        response = self._post("/internal/auth/logout", json={"session_token": session_token})
        return AuthLogoutRead.model_validate(response.json())

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
