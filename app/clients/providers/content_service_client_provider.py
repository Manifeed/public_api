from __future__ import annotations

from shared_backend.clients.content_service_networking_client import (
    ContentServiceNetworkingClient,
    get_content_service_client as get_shared_content_service_client,
    get_required_content_service_client as get_required_shared_content_service_client,
)

from app.clients.networking.service_client_registry import get_service_http_client_registry
from app.clients.networking.service_http_client import _record_upstream_trace


def get_content_service_client() -> ContentServiceNetworkingClient | None:
    registry = get_service_http_client_registry()
    return get_shared_content_service_client(
        http_client=registry.content if registry is not None else None,
        trace_callback=_record_upstream_trace,
    )


def get_required_content_service_client() -> ContentServiceNetworkingClient:
    registry = get_service_http_client_registry()
    return get_required_shared_content_service_client(
        http_client=registry.content if registry is not None else None,
        trace_callback=_record_upstream_trace,
    )
