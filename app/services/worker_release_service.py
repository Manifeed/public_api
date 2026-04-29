from __future__ import annotations

from app.clients.networking.worker_service_networking_client import (
    get_required_worker_service_client,
)
from app.schemas.workers.worker_release_schema import WorkerDesktopReleaseListRead


def list_desktop_releases() -> WorkerDesktopReleaseListRead:
    return get_required_worker_service_client().list_desktop_releases()
