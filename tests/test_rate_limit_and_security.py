from __future__ import annotations

from fastapi import Request
import pytest

from app.clients.networking.redis_networking_client import RedisCommandError
from shared_backend.errors.custom_exceptions import InternalServiceAuthError, RateLimitExceededError
from app.middleware import rate_limit
from shared_backend.security.internal_service_auth import validate_internal_service_token_configuration


def _request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/test",
            "headers": [],
            "client": ("127.0.0.1", 12345),
            "scheme": "http",
            "server": ("testserver", 80),
        }
    )


def test_rate_limit_falls_back_to_memory_when_redis_is_optional(app_env, monkeypatch) -> None:
    monkeypatch.setattr(
        rate_limit.RedisNetworkingClient,
        "increment_with_ttl",
        lambda self, key, ttl_seconds: (_ for _ in ()).throw(RedisCommandError("redis down")),
    )

    rate_limit.enforce_rate_limit(
        _request(),
        namespace="optional",
        limit=2,
        window_seconds=60,
    )


def test_rate_limit_fails_closed_when_redis_is_required(app_env, monkeypatch) -> None:
    monkeypatch.setenv("RATE_LIMIT_REDIS_REQUIRED", "true")
    monkeypatch.setattr(
        rate_limit.RedisNetworkingClient,
        "increment_with_ttl",
        lambda self, key, ttl_seconds: (_ for _ in ()).throw(RedisCommandError("redis down")),
    )

    with pytest.raises(RateLimitExceededError):
        rate_limit.enforce_rate_limit(
            _request(),
            namespace="strict",
            limit=2,
            window_seconds=60,
        )


def test_require_internal_service_token_true_overrides_dev_environment(app_env, monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.setenv("REQUIRE_INTERNAL_SERVICE_TOKEN", "true")
    monkeypatch.delenv("INTERNAL_SERVICE_TOKEN", raising=False)

    with pytest.raises(InternalServiceAuthError):
        validate_internal_service_token_configuration()
