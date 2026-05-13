from __future__ import annotations

from app.clients.networking import redis_networking_client
from shared_backend.schemas.internal.service_schema import InternalServiceHealthRead
from app.services import readiness_service

from .conftest import client_context


class _HealthyClient:
    def __init__(self, status: str = "ok") -> None:
        self._status = status

    def read_internal_health(self) -> InternalServiceHealthRead:
        return InternalServiceHealthRead(service="upstream", status=self._status)


def test_internal_ready_is_green_when_config_and_dependencies_are_valid(
    app_env,
    monkeypatch,
) -> None:
    monkeypatch.setattr(readiness_service, "get_auth_service_client", lambda: _HealthyClient())
    monkeypatch.setattr(readiness_service, "get_user_service_client", lambda: _HealthyClient())
    monkeypatch.setattr(readiness_service, "get_admin_service_client", lambda: _HealthyClient())
    monkeypatch.setattr(readiness_service, "get_content_service_client", lambda: _HealthyClient())
    monkeypatch.setattr(readiness_service, "get_worker_service_client", lambda: _HealthyClient())
    monkeypatch.setattr(redis_networking_client, "get_redis_client", lambda config=None: object())
    monkeypatch.setattr(redis_networking_client.RedisNetworkingClient, "ping", lambda self: "PONG")

    with client_context() as client:
        response = client.get("/internal/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["dependencies"]["redis"]["status"] == "ready"


def test_internal_ready_fails_when_required_config_is_missing(
    app_env,
    monkeypatch,
) -> None:
    monkeypatch.delenv("AUTH_SERVICE_URL", raising=False)
    monkeypatch.setattr(readiness_service, "get_auth_service_client", lambda: None)
    monkeypatch.setattr(readiness_service, "get_user_service_client", lambda: _HealthyClient())
    monkeypatch.setattr(readiness_service, "get_admin_service_client", lambda: _HealthyClient())
    monkeypatch.setattr(readiness_service, "get_content_service_client", lambda: _HealthyClient())
    monkeypatch.setattr(readiness_service, "get_worker_service_client", lambda: _HealthyClient())
    monkeypatch.setattr(redis_networking_client.RedisNetworkingClient, "ping", lambda self: "PONG")

    with client_context() as client:
        response = client.get("/internal/ready")

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "not_ready"
    assert payload["dependencies"]["auth_service"]["status"] == "not_ready"
