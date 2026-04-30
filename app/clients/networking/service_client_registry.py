from __future__ import annotations

from dataclasses import dataclass

import httpx


DEFAULT_MAX_CONNECTIONS = 100
DEFAULT_MAX_KEEPALIVE_CONNECTIONS = 20
DEFAULT_KEEPALIVE_EXPIRY_SECONDS = 30.0


@dataclass
class ServiceHttpClientRegistry:
    auth: httpx.Client
    user: httpx.Client
    admin: httpx.Client
    content: httpx.Client
    worker: httpx.Client

    def close(self) -> None:
        for client in (self.auth, self.user, self.admin, self.content, self.worker):
            client.close()


_registry: ServiceHttpClientRegistry | None = None


def initialize_service_http_client_registry() -> ServiceHttpClientRegistry:
    global _registry
    if _registry is None:
        _registry = ServiceHttpClientRegistry(
            auth=_build_http_client(),
            user=_build_http_client(),
            admin=_build_http_client(),
            content=_build_http_client(),
            worker=_build_http_client(),
        )
    return _registry


def get_service_http_client_registry() -> ServiceHttpClientRegistry | None:
    return _registry


def close_service_http_client_registry() -> None:
    global _registry
    if _registry is not None:
        _registry.close()
        _registry = None


def _build_http_client() -> httpx.Client:
    return httpx.Client(
        limits=httpx.Limits(
            max_connections=DEFAULT_MAX_CONNECTIONS,
            max_keepalive_connections=DEFAULT_MAX_KEEPALIVE_CONNECTIONS,
            keepalive_expiry=DEFAULT_KEEPALIVE_EXPIRY_SECONDS,
        ),
    )
