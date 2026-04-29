from __future__ import annotations

from typing import Any

import httpx

from app.clients.networking.service_http_client import (
    ServiceClientConfig,
    build_service_config,
    request_service,
    require_service_client,
)
from app.schemas.admin.admin_stats_schema import AdminStatsRead
from app.schemas.admin.admin_user_schema import (
    AdminUserListRead,
    AdminUserRead,
    AdminUserUpdateRequestSchema,
)
from app.schemas.analytics.analysis_schema import AnalysisOverviewRead, SimilarSourcesRead
from app.schemas.auth.auth_schema import UserRole
from app.schemas.health import HealthRead
from app.schemas.jobs.job_automation_schema import (
    JobAutomationRead,
    JobAutomationUpdateRequestSchema,
)
from app.schemas.jobs.job_enqueue_schema import (
    JobEnqueueRead,
    RssScrapeJobCreateRequestSchema,
    SourceEmbeddingJobCreateRequestSchema,
)
from app.schemas.jobs.job_schema import JobStatusRead, JobTaskRead, JobsOverviewRead
from app.schemas.rss.rss_company_schema import RssCompanyRead
from app.schemas.rss.rss_enabled_toggle_schema import (
    RssCompanyEnabledToggleRead,
    RssEnabledTogglePayload,
    RssFeedEnabledToggleRead,
)
from app.schemas.rss.rss_feed_schema import RssFeedRead
from app.schemas.rss.rss_sync_schema import RssSyncRead


class AdminServiceNetworkingClient:
    def __init__(self, config: ServiceClientConfig, http_client: httpx.Client | None = None) -> None:
        self._config = config
        self._http_client = http_client

    @classmethod
    def from_env(cls) -> "AdminServiceNetworkingClient | None":
        config = build_service_config(
            base_url_env="ADMIN_SERVICE_URL",
            timeout_env="ADMIN_SERVICE_TIMEOUT_SECONDS",
            default_timeout_seconds=10.0,
            service_name="Admin",
        )
        return cls(config) if config is not None else None

    def read_admin_users(
        self,
        *,
        role: UserRole | None,
        is_active: bool | None,
        api_access_enabled: bool | None,
        search: str | None,
        limit: int,
        offset: int,
    ) -> AdminUserListRead:
        response = self._get(
            "/internal/admin/users",
            params={
                "role": role,
                "is_active": is_active,
                "api_access_enabled": api_access_enabled,
                "search": search,
                "limit": limit,
                "offset": offset,
            },
        )
        return AdminUserListRead.model_validate(response.json())

    def update_admin_user(self, *, user_id: int, payload: AdminUserUpdateRequestSchema) -> AdminUserRead:
        response = self._patch(
            f"/internal/admin/users/{user_id}",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return AdminUserRead.model_validate(response.json())

    def read_admin_stats(self) -> AdminStatsRead:
        response = self._get("/internal/admin/stats")
        return AdminStatsRead.model_validate(response.json())

    def read_health(self) -> HealthRead:
        response = self._get("/internal/admin/health/")
        return HealthRead.model_validate(response.json())

    def read_analysis_overview(self) -> AnalysisOverviewRead:
        response = self._get("/internal/admin/analysis/overview")
        return AnalysisOverviewRead.model_validate(response.json())

    def read_similar_sources(
        self,
        *,
        source_id: int,
        limit: int,
        worker_version: str | None,
    ) -> SimilarSourcesRead:
        response = self._get(
            "/internal/admin/analysis/similar-sources",
            params={"source_id": source_id, "limit": limit, "worker_version": worker_version},
        )
        return SimilarSourcesRead.model_validate(response.json())

    def list_rss_companies(self) -> list[RssCompanyRead]:
        response = self._get("/internal/admin/rss/companies")
        return [RssCompanyRead.model_validate(item) for item in response.json()]

    def list_rss_feeds(self, *, company_id: int | None) -> list[RssFeedRead]:
        response = self._get("/internal/admin/rss/", params={"company_id": company_id})
        return [RssFeedRead.model_validate(item) for item in response.json()]

    def sync_rss_catalog(self, *, force: bool) -> RssSyncRead:
        response = self._post("/internal/admin/rss/sync", params={"force": force}, json=None)
        return RssSyncRead.model_validate(response.json())

    def toggle_rss_feed_enabled(
        self,
        *,
        feed_id: int,
        payload: RssEnabledTogglePayload,
    ) -> RssFeedEnabledToggleRead:
        response = self._patch(
            f"/internal/admin/rss/feeds/{feed_id}/enabled",
            json=payload.model_dump(mode="json"),
        )
        return RssFeedEnabledToggleRead.model_validate(response.json())

    def toggle_rss_company_enabled(
        self,
        *,
        company_id: int,
        payload: RssEnabledTogglePayload,
    ) -> RssCompanyEnabledToggleRead:
        response = self._patch(
            f"/internal/admin/rss/companies/{company_id}/enabled",
            json=payload.model_dump(mode="json"),
        )
        return RssCompanyEnabledToggleRead.model_validate(response.json())

    def list_jobs(self, *, limit: int) -> JobsOverviewRead:
        response = self._get("/internal/admin/jobs", params={"limit": limit})
        return JobsOverviewRead.model_validate(response.json())

    def enqueue_rss_scrape_job(self, payload: RssScrapeJobCreateRequestSchema | None) -> JobEnqueueRead:
        response = self._post(
            "/internal/admin/jobs/rss-scrape",
            json=(payload.model_dump(mode="json") if payload is not None else None),
        )
        return JobEnqueueRead.model_validate(response.json())

    def enqueue_source_embedding_job(
        self,
        payload: SourceEmbeddingJobCreateRequestSchema | None,
    ) -> JobEnqueueRead:
        response = self._post(
            "/internal/admin/jobs/source-embedding",
            json=(payload.model_dump(mode="json") if payload is not None else None),
        )
        return JobEnqueueRead.model_validate(response.json())

    def read_job_automation(self) -> JobAutomationRead:
        response = self._get("/internal/admin/jobs/automation")
        return JobAutomationRead.model_validate(response.json())

    def update_job_automation(self, payload: JobAutomationUpdateRequestSchema) -> JobAutomationRead:
        response = self._patch("/internal/admin/jobs/automation", json=payload.model_dump(mode="json"))
        return JobAutomationRead.model_validate(response.json())

    def list_job_tasks(self, *, job_id: str) -> list[JobTaskRead]:
        response = self._get(f"/internal/admin/jobs/{job_id}/tasks")
        return [JobTaskRead.model_validate(item) for item in response.json()]

    def read_job_status(self, *, job_id: str) -> JobStatusRead:
        response = self._get(f"/internal/admin/jobs/{job_id}")
        return JobStatusRead.model_validate(response.json())

    def _get(self, path: str, *, params: dict[str, Any] | None = None) -> httpx.Response:
        return request_service(
            config=self._config,
            method="GET",
            path=path,
            params=params,
            http_client=self._http_client,
        )

    def _post(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        return request_service(
            config=self._config,
            method="POST",
            path=path,
            params=params,
            json=json,
            http_client=self._http_client,
        )

    def _patch(self, path: str, *, json: dict[str, Any]) -> httpx.Response:
        return request_service(
            config=self._config,
            method="PATCH",
            path=path,
            json=json,
            http_client=self._http_client,
        )


def get_admin_service_client() -> AdminServiceNetworkingClient | None:
    return AdminServiceNetworkingClient.from_env()


def get_required_admin_service_client() -> AdminServiceNetworkingClient:
    return require_service_client(get_admin_service_client(), env_name="ADMIN_SERVICE_URL")
