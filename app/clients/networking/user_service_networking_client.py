from __future__ import annotations

from app.clients.networking.service_client_registry import get_service_http_client_registry
from app.clients.networking.service_http_client import require_service_client
from app.observability.request_context import UpstreamCallTrace, record_upstream_call

from shared_backend.clients.service_http_client import ServiceRequestTrace
from shared_backend.clients.user_service_networking_client import UserServiceNetworkingClient


def _record_upstream_trace(trace: ServiceRequestTrace) -> None:
    record_upstream_call(
        UpstreamCallTrace(
            service=trace.service,
            method=trace.method,
            path=trace.path,
            status=trace.status,
            latency_ms=trace.latency_ms,
            outcome=trace.outcome,
            error=trace.error,
        )
    )


def get_user_service_client() -> UserServiceNetworkingClient | None:
    registry = get_service_http_client_registry()
    return UserServiceNetworkingClient.from_env(
        http_client=registry.user if registry is not None else None,
        trace_callback=_record_upstream_trace,
    )


def get_required_user_service_client() -> UserServiceNetworkingClient:
    return require_service_client(
        get_user_service_client(),
        env_name="USER_SERVICE_URL",
    )


__all__ = [
    "UserServiceNetworkingClient",
    "get_required_user_service_client",
    "get_user_service_client",
]
