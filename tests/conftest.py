from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.dependencies.auth_dependencies import (
    require_authenticated_user,
    require_masked_admin_user,
)
from app.main import create_app

from shared_backend.domain.current_user import AuthenticatedUserContext
from shared_backend.schemas.auth.auth_schema import AuthenticatedUserRead


@pytest.fixture
def app_env(monkeypatch: pytest.MonkeyPatch) -> None:
    values = {
        "APP_ENV": "test",
        "AUTH_SERVICE_URL": "http://auth-service:8000",
        "USER_SERVICE_URL": "http://user-service:8000",
        "ADMIN_SERVICE_URL": "http://admin-service:8000",
        "CONTENT_SERVICE_URL": "http://content-service:8000",
        "WORKER_SERVICE_URL": "http://worker-service:8000",
        "INTERNAL_SERVICE_TOKEN": "x" * 32,
        "CORS_ORIGINS": "http://frontend.test",
        "PUBLIC_BASE_URL": "https://public.example.test",
        "CSRF_TRUSTED_ORIGINS": "http://frontend.test",
        "RATE_LIMIT_ENABLED": "false",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def authenticated_user() -> AuthenticatedUserContext:
    return AuthenticatedUserContext(
        user_id=1,
        email="user@example.com",
        role="user",
        is_active=True,
        api_access_enabled=True,
        session_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )


@pytest.fixture
def admin_user() -> AuthenticatedUserContext:
    return AuthenticatedUserContext(
        user_id=2,
        email="admin@example.com",
        role="admin",
        is_active=True,
        api_access_enabled=True,
        session_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )


@pytest.fixture
def sample_auth_user() -> AuthenticatedUserRead:
    now = datetime.now(timezone.utc)
    return AuthenticatedUserRead(
        id=1,
        email="user@example.com",
        pseudo="user",
        pp_id=1,
        role="user",
        is_active=True,
        api_access_enabled=True,
        created_at=now,
        updated_at=now,
    )


@contextmanager
def client_context():
    app = create_app()
    with TestClient(app) as client:
        yield client


def override_authenticated_user(app, user: AuthenticatedUserContext) -> None:
    app.dependency_overrides[require_authenticated_user] = lambda: user


def override_masked_admin_user(app, user: AuthenticatedUserContext) -> None:
    app.dependency_overrides[require_masked_admin_user] = lambda: user
