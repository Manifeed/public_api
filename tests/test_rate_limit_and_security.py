from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.clients.networking.redis_networking_client import RedisCommandError
from shared_backend.errors.custom_exceptions import InternalServiceAuthError, RateLimitExceededError
from app.middleware import rate_limit
from app.main import create_app
from shared_backend.security.internal_service_auth import validate_internal_service_token_configuration


def test_rate_limit_fails_closed_when_redis_is_unreachable(app_env, monkeypatch) -> None:
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setattr(
        rate_limit.RedisNetworkingClient,
        "increment_with_ttl",
        lambda self, key, ttl_seconds: (_ for _ in ()).throw(RedisCommandError("redis down")),
    )

    with pytest.raises(RateLimitExceededError):
        rate_limit.enforce_rate_limit(
            namespace="strict",
            identifier="user@example.com",
            limit=2,
            window_seconds=60,
        )


def test_internal_service_token_must_be_configured(app_env, monkeypatch) -> None:
    monkeypatch.delenv("INTERNAL_SERVICE_TOKEN", raising=False)
    monkeypatch.delenv("INTERNAL_SERVICE_TOKENS", raising=False)

    with pytest.raises(InternalServiceAuthError):
        validate_internal_service_token_configuration()


def test_public_base_url_must_be_https_in_production(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("PUBLIC_BASE_URL", "http://public.example.test")
    monkeypatch.setenv("INTERNAL_SERVICE_TOKEN", "x" * 32)

    with pytest.raises(RuntimeError):
        create_app()


def test_public_api_startup_fails_when_internal_token_is_missing(app_env, monkeypatch) -> None:
    monkeypatch.delenv("INTERNAL_SERVICE_TOKEN", raising=False)
    monkeypatch.delenv("INTERNAL_SERVICE_TOKENS", raising=False)

    with pytest.raises(InternalServiceAuthError):
        with TestClient(create_app()):
            pass
