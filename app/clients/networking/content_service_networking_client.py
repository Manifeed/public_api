from __future__ import annotations

from typing import Any

import httpx

from app.clients.networking.service_http_client import (
    ServiceClientConfig,
    build_service_config,
    request_service,
    require_service_client,
)
from app.schemas.analytics.analysis_schema import SimilarSourcesRead
from app.schemas.sources.source_schema import (
    RssSourceDetailRead,
    RssSourcePageRead,
    UserSourceDetailRead,
    UserSourcePageRead,
)


class ContentImageRead:
    def __init__(self, *, content: bytes, media_type: str | None, filename: str | None) -> None:
        self.content = content
        self.media_type = media_type
        self.filename = filename


class ContentServiceNetworkingClient:
    def __init__(self, config: ServiceClientConfig, http_client: httpx.Client | None = None) -> None:
        self._config = config
        self._http_client = http_client

    @classmethod
    def from_env(cls) -> "ContentServiceNetworkingClient | None":
        config = build_service_config(
            base_url_env="CONTENT_SERVICE_URL",
            timeout_env="CONTENT_SERVICE_TIMEOUT_SECONDS",
            default_timeout_seconds=10.0,
            service_name="Content",
        )
        return cls(config) if config is not None else None

    def list_admin_sources(
        self,
        *,
        limit: int,
        offset: int,
        author_id: int | None,
    ) -> RssSourcePageRead:
        response = self._get(
            "/internal/content/admin/sources/",
            params={"limit": limit, "offset": offset, "author_id": author_id},
        )
        return RssSourcePageRead.model_validate(response.json())

    def list_admin_sources_by_feed(
        self,
        *,
        feed_id: int,
        limit: int,
        offset: int,
        author_id: int | None,
    ) -> RssSourcePageRead:
        response = self._get(
            f"/internal/content/admin/sources/feeds/{feed_id}",
            params={"limit": limit, "offset": offset, "author_id": author_id},
        )
        return RssSourcePageRead.model_validate(response.json())

    def list_admin_sources_by_company(
        self,
        *,
        company_id: int,
        limit: int,
        offset: int,
        author_id: int | None,
    ) -> RssSourcePageRead:
        response = self._get(
            f"/internal/content/admin/sources/companies/{company_id}",
            params={"limit": limit, "offset": offset, "author_id": author_id},
        )
        return RssSourcePageRead.model_validate(response.json())

    def read_admin_source(self, *, source_id: int) -> RssSourceDetailRead:
        response = self._get(f"/internal/content/admin/sources/{source_id}")
        return RssSourceDetailRead.model_validate(response.json())

    def list_user_sources(self, *, limit: int, offset: int) -> UserSourcePageRead:
        response = self._get(
            "/internal/content/sources/",
            params={"limit": limit, "offset": offset},
        )
        return UserSourcePageRead.model_validate(response.json())

    def read_user_source(self, *, source_id: int) -> UserSourceDetailRead:
        response = self._get(f"/internal/content/sources/{source_id}")
        return UserSourceDetailRead.model_validate(response.json())

    def read_similar_sources(
        self,
        *,
        source_id: int,
        limit: int,
        worker_version: str | None,
    ) -> SimilarSourcesRead:
        response = self._get(
            f"/internal/content/sources/{source_id}/similar",
            params={"limit": limit, "worker_version": worker_version},
        )
        return SimilarSourcesRead.model_validate(response.json())

    def read_rss_icon(self, *, icon_url: str) -> ContentImageRead:
        response = self._get(f"/internal/content/rss/img/{icon_url}")
        content_disposition = response.headers.get("content-disposition", "")
        return ContentImageRead(
            content=response.content,
            media_type=response.headers.get("content-type"),
            filename=_parse_filename(content_disposition),
        )

    def _get(self, path: str, *, params: dict[str, Any] | None = None) -> httpx.Response:
        return request_service(
            config=self._config,
            method="GET",
            path=path,
            params=params,
            http_client=self._http_client,
        )


def get_content_service_client() -> ContentServiceNetworkingClient | None:
    return ContentServiceNetworkingClient.from_env()


def get_required_content_service_client() -> ContentServiceNetworkingClient:
    return require_service_client(get_content_service_client(), env_name="CONTENT_SERVICE_URL")


def _parse_filename(content_disposition: str) -> str | None:
    for part in content_disposition.split(";"):
        key, _, value = part.strip().partition("=")
        if key.lower() == "filename" and value:
            return value.strip('"')
    return None
