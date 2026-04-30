from __future__ import annotations

import json
import logging
from time import perf_counter

from fastapi import Request

from app.observability.request_context import (
    begin_request_log_context,
    end_request_log_context,
    get_request_log_context,
)


logger = logging.getLogger("manifeed.public_api")


async def observability_middleware(request: Request, call_next):
    token = begin_request_log_context()
    started_at = perf_counter()
    response = None
    try:
        response = await call_next(request)
        return response
    finally:
        latency_ms = max(0, round((perf_counter() - started_at) * 1000))
        context = get_request_log_context()
        if context is not None:
            payload = {
                "event": "public_api_request",
                "method": request.method,
                "path": request.url.path,
                "query": request.url.query,
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
            logger.info(json.dumps(payload, separators=(",", ":"), sort_keys=True))
        end_request_log_context(token)
