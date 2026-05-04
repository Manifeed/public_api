from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx

from app.clients.networking import admin_service_networking_client
from app.clients.networking.admin_service_networking_client import AdminServiceNetworkingClient
from shared_backend.clients.service_http_client import ServiceClientConfig
from shared_backend.domain.current_user import AuthenticatedUserContext
from shared_backend.schemas.admin.admin_user_schema import AdminUserUpdateRequestSchema


def _config() -> ServiceClientConfig:
    return ServiceClientConfig(
        base_url="http://admin-service:8000",
        internal_token="x" * 32,
        timeout_seconds=5.0,
        service_name="Admin",
    )


def _current_user() -> AuthenticatedUserContext:
    return AuthenticatedUserContext(
        user_id=2,
        email="admin@example.com",
        role="admin",
        is_active=True,
        api_access_enabled=True,
        session_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )


def test_read_admin_users_wraps_current_user_and_filters(monkeypatch) -> None:
    seen: dict[str, object] = {}

    def fake_request_service(**kwargs) -> httpx.Response:
        seen.update(kwargs)
        return httpx.Response(
            200,
            json={"items": [], "total": 0, "active_total": 0, "limit": 10, "offset": 5},
            request=httpx.Request("POST", "http://admin-service:8000/internal/admin/users/list"),
        )

    monkeypatch.setattr(admin_service_networking_client, "request_service", fake_request_service)
    client = AdminServiceNetworkingClient(_config())
    current_user = _current_user()

    response = client.read_admin_users(
        current_user=current_user,
        role="user",
        is_active=True,
        api_access_enabled=False,
        search="alice",
        limit=10,
        offset=5,
    )

    assert response.total == 0
    assert seen["path"] == "/internal/admin/users/list"
    assert seen["json"] == {
        "payload": {
            "current_user": {
                "user_id": current_user.user_id,
                "email": current_user.email,
                "role": current_user.role,
                "is_active": current_user.is_active,
                "api_access_enabled": current_user.api_access_enabled,
                "session_expires_at": current_user.session_expires_at.isoformat(),
            },
            "filters": {
                "role": "user",
                "is_active": True,
                "api_access_enabled": False,
                "search": "alice",
                "limit": 10,
                "offset": 5,
            },
        }
    }


def test_update_admin_user_wraps_current_user_and_payload(monkeypatch) -> None:
    seen: dict[str, object] = {}

    def fake_request_service(**kwargs) -> httpx.Response:
        seen.update(kwargs)
        return httpx.Response(
            200,
            json={
                "id": 3,
                "email": "user@example.com",
                "pseudo": "user",
                "role": "user",
                "is_active": False,
                "api_access_enabled": True,
            },
            request=httpx.Request("PATCH", "http://admin-service:8000/internal/admin/users/3"),
        )

    monkeypatch.setattr(admin_service_networking_client, "request_service", fake_request_service)
    client = AdminServiceNetworkingClient(_config())
    current_user = _current_user()
    payload = AdminUserUpdateRequestSchema(is_active=False)

    response = client.update_admin_user(current_user=current_user, user_id=3, payload=payload)

    assert response.id == 3
    assert seen["path"] == "/internal/admin/users/3"
    assert seen["json"] == {
        "payload": {
            "current_user": {
                "user_id": current_user.user_id,
                "email": current_user.email,
                "role": current_user.role,
                "is_active": current_user.is_active,
                "api_access_enabled": current_user.api_access_enabled,
                "session_expires_at": current_user.session_expires_at.isoformat(),
            },
            "payload": {
                "is_active": False,
            },
        }
    }
