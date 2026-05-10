from app.clients.providers.content_service_client_provider import get_required_content_service_client

from shared_backend.schemas.analytics.analysis_schema import SimilarSourcesRead
from shared_backend.schemas.sources.source_schema import (
    RssSourceDetailRead,
    RssSourcePageRead,
    UserSourceDetailRead,
    UserSourcePageRead,
    UserSourceSearchPageRead,
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


def search_user_sources(
    *,
    q: str | None,
    limit: int,
    offset: int,
    country: str | None,
    company_id: int | None,
    author_id: int | None,
    period: str | None,
) -> UserSourceSearchPageRead:
    return get_required_content_service_client().search_user_sources(
        q=q,
        limit=limit,
        offset=offset,
        country=country,
        company_id=company_id,
        author_id=author_id,
        period=period,
    )


def read_user_source(*, source_id: int) -> UserSourceDetailRead:
    return get_required_content_service_client().read_user_source(source_id=source_id)


def read_similar_sources(
    *,
    source_id: int,
    limit: int,
) -> SimilarSourcesRead:
    return get_required_content_service_client().read_similar_sources(
        source_id=source_id,
        limit=limit,
    )
