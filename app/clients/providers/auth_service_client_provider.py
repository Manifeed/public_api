from __future__ import annotations

from app.clients.networking.service_client_registry import get_service_http_client_registry
from app.clients.networking.service_http_client import _record_upstream_trace, require_service_client

from shared_backend.clients.auth_service_networking_client import AuthServiceNetworkingClient


def get_auth_service_client() -> AuthServiceNetworkingClient | None:
    registry = get_service_http_client_registry()
    return AuthServiceNetworkingClient.from_env(
        http_client=registry.auth if registry is not None else None,
        trace_callback=_record_upstream_trace,
    )


def get_required_auth_service_client() -> AuthServiceNetworkingClient:
    return require_service_client(
        get_auth_service_client(),
        env_name="AUTH_SERVICE_URL",
    )
