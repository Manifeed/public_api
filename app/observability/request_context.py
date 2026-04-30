from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass, field
from time import perf_counter


@dataclass
class UpstreamCallTrace:
    service: str
    method: str
    path: str
    status: int | None
    latency_ms: int
    outcome: str
    error: str | None = None


@dataclass
class RequestLogContext:
    started_at: float = field(default_factory=perf_counter)
    route_class: str = "public-api"
    rate_limit_blocked: bool = False
    csrf_denied: bool = False
    upstream_calls: list[UpstreamCallTrace] = field(default_factory=list)


_request_log_context: ContextVar[RequestLogContext | None] = ContextVar(
    "public_api_request_log_context",
    default=None,
)


def begin_request_log_context() -> object:
    return _request_log_context.set(RequestLogContext())


def end_request_log_context(token: object) -> None:
    _request_log_context.reset(token)


def get_request_log_context() -> RequestLogContext | None:
    return _request_log_context.get()


def mark_rate_limit_blocked() -> None:
    context = get_request_log_context()
    if context is not None:
        context.rate_limit_blocked = True


def mark_csrf_denied() -> None:
    context = get_request_log_context()
    if context is not None:
        context.csrf_denied = True


def record_upstream_call(trace: UpstreamCallTrace) -> None:
    context = get_request_log_context()
    if context is not None:
        context.upstream_calls.append(trace)
