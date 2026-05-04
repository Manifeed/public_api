from urllib.parse import urlparse

from fastapi import APIRouter

from app.services.worker_release_service import list_desktop_releases

from shared_backend.schemas.workers.worker_release_schema import WorkerDesktopReleaseListRead
from shared_backend.utils.public_url import build_public_url, require_public_base_url


worker_release_router = APIRouter(prefix="/workers/api", tags=["workers-release"])


@worker_release_router.get("/releases/desktop", response_model=WorkerDesktopReleaseListRead)
def list_public_desktop_releases() -> WorkerDesktopReleaseListRead:
    releases = list_desktop_releases()
    public_base_url = require_public_base_url()
    return releases.model_copy(
        update={
            "items": [
                item.model_copy(
                    update={
                        "download_url": build_public_url(
                            public_base_url,
                            _resolve_download_path(item.artifact_name, item.download_url),
                        ),
                        "release_notes_url": item.release_notes_url,
                    }
                )
                for item in releases.items
            ]
        }
    )


def _resolve_download_path(artifact_name: str, download_url: str) -> str:
    parsed = urlparse(download_url)
    if parsed.path.startswith("/workers/api/releases/download/"):
        return parsed.path
    return f"/workers/api/releases/download/{artifact_name}"
