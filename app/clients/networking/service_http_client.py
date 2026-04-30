from __future__ import annotations

from typing import Any

import httpx

from shared_backend.errors.app_error import AppError, UpstreamServiceError
from app.observability.request_context import UpstreamCallTrace, record_upstream_call

from shared_backend.clients.service_http_client import (
    ServiceClientConfig,
    ServiceRequestTrace,
    build_internal_headers,
    build_service_config,
    raise_for_service_error as shared_raise_for_service_error,
    request_service as shared_request_service,
    require_service_client as shared_require_service_client,
)


def request_service(
    *,
    config: ServiceClientConfig,
    method: str,
    path: str,
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
    http_client: httpx.Client | None = None,
) -> httpx.Response:
    return shared_request_service(
        config=config,
        method=method,
        path=path,
        params=params,
        json=json,
        http_client=http_client,
        app_error_factory=AppError,
        upstream_error_factory=UpstreamServiceError,
        trace_callback=_record_upstream_trace,
    )


def raise_for_service_error(response: httpx.Response, service_name: str) -> None:
    shared_raise_for_service_error(
        response,
        service_name=service_name,
        app_error_factory=AppError,
        upstream_error_factory=UpstreamServiceError,
    )


def require_service_client(client: Any | None, *, env_name: str) -> Any:
    return shared_require_service_client(
        client,
        env_name=env_name,
        upstream_error_factory=UpstreamServiceError,
    )


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
