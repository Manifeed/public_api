from __future__ import annotations

import os

from app.clients.networking.redis_networking_client import (
    RedisCommandError,
    RedisNetworkingClient,
)
from shared_backend.errors.custom_exceptions import RateLimitExceededError
from app.observability.request_context import mark_rate_limit_blocked


def enforce_rate_limit(
    *,
    namespace: str,
    identifier: str,
    limit: int,
    window_seconds: int,
) -> None:
    if not is_rate_limit_enabled():
        return

    key = _build_rate_limit_key(
        namespace=namespace,
        identifier=identifier,
    )
    count = _increment_redis_bucket(key, window_seconds)
    if count is None:
        mark_rate_limit_blocked()
        raise RateLimitExceededError("Rate limiting is temporarily unavailable")
    if count > limit:
        mark_rate_limit_blocked()
        raise RateLimitExceededError()


def is_rate_limit_enabled() -> bool:
    raw_value = os.getenv("RATE_LIMIT_ENABLED", "true")
    return raw_value.strip().lower() not in {"0", "false", "no", "off"}


def _build_rate_limit_key(*, namespace: str, identifier: str) -> str:
    safe_identifier = identifier.strip().lower() or "unknown"
    return f"manifeed:rate-limit:{namespace}:{safe_identifier}"


def _increment_redis_bucket(key: str, window_seconds: int) -> int | None:
    try:
        return RedisNetworkingClient().increment_with_ttl(key, window_seconds)
    except RedisCommandError:
        return None
