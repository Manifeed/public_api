from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.dependencies.auth_dependencies import require_masked_admin_user
from app.services import rss_service

from shared_backend.schemas.rss.rss_company_schema import RssCompanyRead
from shared_backend.schemas.rss.rss_enabled_toggle_schema import (
    RssCompanyEnabledToggleRead,
    RssEnabledTogglePayload,
    RssFeedEnabledToggleRead,
)
from shared_backend.schemas.rss.rss_feed_schema import RssFeedRead
from shared_backend.schemas.rss.rss_sync_schema import RssSyncRead


rss_admin_router = APIRouter(
    prefix="/api/admin/rss",
    tags=["rss"],
    dependencies=[Depends(require_masked_admin_user)],
)


@rss_admin_router.get("/companies", response_model=list[RssCompanyRead])
def read_rss_companies() -> list[RssCompanyRead]:
    return rss_service.list_rss_companies()


@rss_admin_router.get("/", response_model=list[RssFeedRead])
def read_rss_feeds(
    company_id: Annotated[int | None, Query(ge=1)] = None,
) -> list[RssFeedRead]:
    return rss_service.list_rss_feeds(company_id=company_id)


@rss_admin_router.post("/sync", response_model=RssSyncRead)
def sync_rss_feeds(
    force: bool = Query(default=False, description="Force full catalog reprocessing"),
) -> RssSyncRead:
    return rss_service.sync_rss_catalog(force=force)


@rss_admin_router.patch("/feeds/{feed_id}/enabled", response_model=RssFeedEnabledToggleRead)
def update_rss_feed_enabled(
    payload: RssEnabledTogglePayload,
    feed_id: Annotated[int, Path(ge=1)],
) -> RssFeedEnabledToggleRead:
    return rss_service.toggle_rss_feed_enabled(feed_id=feed_id, payload=payload)


@rss_admin_router.patch("/companies/{company_id}/enabled", response_model=RssCompanyEnabledToggleRead)
def update_rss_company_enabled(
    payload: RssEnabledTogglePayload,
    company_id: Annotated[int, Path(ge=1)],
) -> RssCompanyEnabledToggleRead:
    return rss_service.toggle_rss_company_enabled(company_id=company_id, payload=payload)
