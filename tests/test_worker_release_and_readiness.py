from __future__ import annotations

from datetime import datetime, timezone

from app.clients.networking import redis_networking_client
from app.routers import worker_release_router
from shared_backend.schemas.internal.service_schema import InternalServiceHealthRead
from shared_backend.schemas.workers.worker_release_schema import (
    WorkerDesktopReleaseListRead,
    WorkerDesktopReleaseRead,
)
from app.services import readiness_service

from .conftest import client_context


class _HealthyClient:
    def __init__(self, status: str = "ok") -> None:
        self._status = status

    def read_internal_health(self) -> InternalServiceHealthRead:
        return InternalServiceHealthRead(service="upstream", status=self._status)


def test_worker_release_route_rewrites_download_url_but_keeps_release_notes(
    app_env,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        worker_release_router,
        "list_desktop_releases",
        lambda: WorkerDesktopReleaseListRead(
            items=[
                WorkerDesktopReleaseRead(
                    artifact_name="manifeed-worker.deb",
                    family="desktop",
                    product="desktop",
                    platform="linux",
                    arch="x86_64",
                    latest_version="1.2.3",
                    minimum_supported_version="1.0.0",
                    worker_version="1.2.3",
                    artifact_kind="deb",
                    sha256="abc123",
                    runtime_bundle=None,
                    download_auth="public",
                    download_url="https://downloads.example/manifeed-worker.deb",
                    release_notes_url="https://notes.example/releases/1.2.3",
                    published_at=datetime.now(timezone.utc),
                    title="Linux",
                    platform_label="Linux",
                    download_label="Download",
                    install_command=None,
                )
            ]
        ),
    )

    with client_context() as client:
        response = client.get("/workers/api/releases/desktop")

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["download_url"] == (
        "https://public.example.test/workers/api/releases/download/manifeed-worker.deb"
    )
    assert payload["items"][0]["release_notes_url"] == "https://notes.example/releases/1.2.3"


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
