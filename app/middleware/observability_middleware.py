from __future__ import annotations

import logging
from time import perf_counter

from fastapi import Request

from app.observability.request_context import (
    begin_request_log_context,
    end_request_log_context,
    get_request_log_context,
)
from shared_backend.utils.logging_utils import (
    DEFAULT_REQUEST_LOG_SKIP_PATHS,
    begin_log_context,
    end_log_context,
    resolve_request_id,
)


logger = logging.getLogger("manifeed.public_api")


async def observability_middleware(request: Request, call_next):
    request_id = resolve_request_id(request)
    shared_log_token = begin_log_context(
        request_id=request_id,
        service_name="public-api",
    )
    request.state.request_id = request_id
    token = begin_request_log_context()
    started_at = perf_counter()
    response = None
    try:
        response = await call_next(request)
        response.headers.setdefault("X-Request-ID", request_id)
        return response
    finally:
        latency_ms = max(0, round((perf_counter() - started_at) * 1000))
        context = get_request_log_context()
        if context is not None and request.url.path not in DEFAULT_REQUEST_LOG_SKIP_PATHS:
            payload = {
                "event": "http_request",
                "route_class": "gateway",
                "method": request.method,
                "path": request.url.path,
                "path_template": _resolve_route_path_template(request),
                "query_keys": sorted(set(request.query_params.keys())),
                "status_code": response.status_code if response is not None else 500,
                "latency_ms": latency_ms,
                "rate_limit_blocked": context.rate_limit_blocked,
                "csrf_denied": context.csrf_denied,
                "upstream_services": sorted({trace.service for trace in context.upstream_calls}),
                "upstream_calls": [
                    {
                        "service": trace.service,
                        "method": trace.method,
                        "path": trace.path,
                        "status": trace.status,
                        "latency_ms": trace.latency_ms,
                        "outcome": trace.outcome,
                        "error": trace.error,
                    }
                    for trace in context.upstream_calls
                ],
            }
            logger.info(payload)
        end_request_log_context(token)
        end_log_context(shared_log_token)


def _resolve_route_path_template(request: Request) -> str:
    route = request.scope.get("route")
    route_path = getattr(route, "path", None)
    if isinstance(route_path, str) and route_path:
        return route_path
    return request.url.path
