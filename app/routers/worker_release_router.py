from urllib.parse import urlparse

from fastapi import APIRouter, Request

from app.schemas.workers.worker_release_schema import WorkerDesktopReleaseListRead
from app.services.worker_release_service import list_desktop_releases


worker_release_router = APIRouter(prefix="/workers/api", tags=["workers-release"])


@worker_release_router.get("/releases/desktop", response_model=WorkerDesktopReleaseListRead)
def list_public_desktop_releases(request: Request) -> WorkerDesktopReleaseListRead:
    releases = list_desktop_releases()
    base_url = str(request.base_url).rstrip("/")
    return releases.model_copy(
        update={
            "items": [
                item.model_copy(
                    update={
                        "download_url": (
                            f"{base_url}"
                            f"{_resolve_download_path(item.artifact_name, item.download_url)}"
                        ),
                        "release_notes_url": f"{base_url}/workers",
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
