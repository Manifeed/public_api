from app.clients.networking.content_service_networking_client import get_required_content_service_client
from app.schemas.analytics.analysis_schema import SimilarSourcesRead
from app.schemas.sources.source_schema import (
    RssSourceDetailRead,
    RssSourcePageRead,
    UserSourceDetailRead,
    UserSourcePageRead,
)


def list_admin_sources(
    *,
    limit: int,
    offset: int,
    author_id: int | None,
) -> RssSourcePageRead:
    return get_required_content_service_client().list_admin_sources(
        limit=limit,
        offset=offset,
        author_id=author_id,
    )


def list_admin_sources_by_feed(
    *,
    feed_id: int,
    limit: int,
    offset: int,
    author_id: int | None,
) -> RssSourcePageRead:
    return get_required_content_service_client().list_admin_sources_by_feed(
        feed_id=feed_id,
        limit=limit,
        offset=offset,
        author_id=author_id,
    )


def list_admin_sources_by_company(
    *,
    company_id: int,
    limit: int,
    offset: int,
    author_id: int | None,
) -> RssSourcePageRead:
    return get_required_content_service_client().list_admin_sources_by_company(
        company_id=company_id,
        limit=limit,
        offset=offset,
        author_id=author_id,
    )


def read_admin_source(*, source_id: int) -> RssSourceDetailRead:
    return get_required_content_service_client().read_admin_source(source_id=source_id)


def list_user_sources(*, limit: int, offset: int) -> UserSourcePageRead:
    return get_required_content_service_client().list_user_sources(limit=limit, offset=offset)


def read_user_source(*, source_id: int) -> UserSourceDetailRead:
    return get_required_content_service_client().read_user_source(source_id=source_id)


def read_similar_sources(
    *,
    source_id: int,
    limit: int,
    worker_version: str | None,
) -> SimilarSourcesRead:
    return get_required_content_service_client().read_similar_sources(
        source_id=source_id,
        limit=limit,
        worker_version=worker_version,
    )
