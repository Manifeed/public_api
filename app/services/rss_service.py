from app.clients.networking.admin_service_networking_client import get_required_admin_service_client
from app.clients.networking.content_service_networking_client import (
    ContentImageRead,
    get_required_content_service_client,
)

from shared_backend.schemas.rss.rss_company_schema import RssCompanyRead
from shared_backend.schemas.rss.rss_enabled_toggle_schema import (
    RssCompanyEnabledToggleRead,
    RssEnabledTogglePayload,
    RssFeedEnabledToggleRead,
)
from shared_backend.schemas.rss.rss_feed_schema import RssFeedRead
from shared_backend.schemas.rss.rss_sync_schema import RssSyncRead


def list_rss_companies() -> list[RssCompanyRead]:
    return get_required_admin_service_client().list_rss_companies()


def list_rss_feeds(*, company_id: int | None) -> list[RssFeedRead]:
    return get_required_admin_service_client().list_rss_feeds(company_id=company_id)


def sync_rss_catalog(*, force: bool) -> RssSyncRead:
    return get_required_admin_service_client().sync_rss_catalog(force=force)


def toggle_rss_feed_enabled(
    *,
    feed_id: int,
    payload: RssEnabledTogglePayload,
) -> RssFeedEnabledToggleRead:
    return get_required_admin_service_client().toggle_rss_feed_enabled(
        feed_id=feed_id,
        payload=payload,
    )


def toggle_rss_company_enabled(
    *,
    company_id: int,
    payload: RssEnabledTogglePayload,
) -> RssCompanyEnabledToggleRead:
    return get_required_admin_service_client().toggle_rss_company_enabled(
        company_id=company_id,
        payload=payload,
    )


def read_rss_icon(*, icon_url: str) -> ContentImageRead:
    return get_required_content_service_client().read_rss_icon(icon_url=icon_url)
