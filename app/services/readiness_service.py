from __future__ import annotations

from time import perf_counter

from app.clients.networking.admin_service_networking_client import get_admin_service_client
from app.clients.networking.auth_service_networking_client import get_auth_service_client
from app.clients.networking.content_service_networking_client import get_content_service_client
from app.clients.networking.redis_networking_client import RedisCommandError, RedisNetworkingClient
from app.clients.networking.user_service_networking_client import get_user_service_client
from app.clients.networking.worker_service_networking_client import get_worker_service_client
from app.middleware.rate_limit import is_rate_limit_enabled, is_redis_required_for_rate_limit
from app.schemas.internal.service_schema import (
    InternalServiceReadyDependencyRead,
    InternalServiceReadyRead,
)
from shared_backend.security.internal_service_auth import validate_internal_service_token_configuration


def read_internal_ready() -> InternalServiceReadyRead:
    dependencies = {
        "internal_service_token": _check_internal_service_token(),
        "auth_service": _check_http_service(
            "auth_service", "http", get_auth_service_client(), env_name="AUTH_SERVICE_URL"
        ),
        "user_service": _check_http_service(
            "user_service", "http", get_user_service_client(), env_name="USER_SERVICE_URL"
        ),
        "admin_service": _check_http_service(
            "admin_service", "http", get_admin_service_client(), env_name="ADMIN_SERVICE_URL"
        ),
        "content_service": _check_http_service(
            "content_service", "http", get_content_service_client(), env_name="CONTENT_SERVICE_URL"
        ),
        "worker_service": _check_http_service(
            "worker_service", "http", get_worker_service_client(), env_name="WORKER_SERVICE_URL"
        ),
        "redis": _check_redis_dependency(),
    }
    overall_status = "ready" if all(item.status == "ready" for item in dependencies.values()) else "not_ready"
    return InternalServiceReadyRead(
        service="public-api",
        status=overall_status,
        dependencies=dependencies,
    )


def _check_internal_service_token() -> InternalServiceReadyDependencyRead:
    started_at = perf_counter()
    try:
        validate_internal_service_token_configuration()
        return InternalServiceReadyDependencyRead(
            name="internal_service_token",
            kind="config",
            status="ready",
            latency_ms=_elapsed_milliseconds(started_at),
        )
    except Exception as exception:
        return InternalServiceReadyDependencyRead(
            name="internal_service_token",
            kind="config",
            status="not_ready",
            detail=str(exception),
            latency_ms=_elapsed_milliseconds(started_at),
        )


def _check_http_service(name: str, kind: str, client, *, env_name: str) -> InternalServiceReadyDependencyRead:
    started_at = perf_counter()
    if client is None:
        return InternalServiceReadyDependencyRead(
            name=name,
            kind=kind,
            status="not_ready",
            detail=f"{env_name} is not configured",
            latency_ms=_elapsed_milliseconds(started_at),
        )

    try:
        response = client.read_internal_health()
        status = "ready" if response.status in {"ok", "ready"} else "not_ready"
        return InternalServiceReadyDependencyRead(
            name=name,
            kind=kind,
            status=status,
            detail=f"upstream_status={response.status}",
            latency_ms=_elapsed_milliseconds(started_at),
        )
    except Exception as exception:
        return InternalServiceReadyDependencyRead(
            name=name,
            kind=kind,
            status="not_ready",
            detail=str(exception),
            latency_ms=_elapsed_milliseconds(started_at),
        )


def _check_redis_dependency() -> InternalServiceReadyDependencyRead:
    started_at = perf_counter()
    if not is_rate_limit_enabled():
        return InternalServiceReadyDependencyRead(
            name="redis",
            kind="redis",
            status="ready",
            detail="rate_limit_disabled",
            latency_ms=_elapsed_milliseconds(started_at),
        )

    try:
        ping_response = RedisNetworkingClient().ping()
        detail = f"ping={ping_response.lower()}"
        if not is_redis_required_for_rate_limit():
            detail = f"{detail} fallback_allowed"
        return InternalServiceReadyDependencyRead(
            name="redis",
            kind="redis",
            status="ready",
            detail=detail,
            latency_ms=_elapsed_milliseconds(started_at),
        )
    except (RedisCommandError, RuntimeError) as exception:
        status = "not_ready" if is_redis_required_for_rate_limit() else "ready"
        detail = str(exception)
        if status == "ready":
            detail = f"{detail} fallback_allowed"
        return InternalServiceReadyDependencyRead(
            name="redis",
            kind="redis",
            status=status,
            detail=detail,
            latency_ms=_elapsed_milliseconds(started_at),
        )


def _elapsed_milliseconds(started_at: float) -> int:
    return max(0, round((perf_counter() - started_at) * 1000))
