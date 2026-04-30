from fastapi import APIRouter, Depends, Path, Query

from app.dependencies.auth_dependencies import require_authenticated_user, require_masked_admin_user
from app.services import sources_service

from shared_backend.schemas.analytics.analysis_schema import SimilarSourcesRead
from shared_backend.schemas.sources.source_schema import (
    RssSourceDetailRead,
    RssSourcePageRead,
    UserSourceDetailRead,
    UserSourcePageRead,
)


admin_sources_router = APIRouter(
    prefix="/api/admin/sources",
    tags=["sources"],
    dependencies=[Depends(require_masked_admin_user)],
)
user_sources_router = APIRouter(
    prefix="/api/sources",
    tags=["sources"],
    dependencies=[Depends(require_authenticated_user)],
)


@admin_sources_router.get("/", response_model=RssSourcePageRead)
def read_admin_sources(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    author_id: int | None = Query(default=None, ge=1),
) -> RssSourcePageRead:
    return sources_service.list_admin_sources(limit=limit, offset=offset, author_id=author_id)


@admin_sources_router.get("/feeds/{feed_id}", response_model=RssSourcePageRead)
def read_admin_sources_by_feed(
    feed_id: int = Path(ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    author_id: int | None = Query(default=None, ge=1),
) -> RssSourcePageRead:
    return sources_service.list_admin_sources_by_feed(
        feed_id=feed_id,
        limit=limit,
        offset=offset,
        author_id=author_id,
    )


@admin_sources_router.get("/companies/{company_id}", response_model=RssSourcePageRead)
def read_admin_sources_by_company(
    company_id: int = Path(ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    author_id: int | None = Query(default=None, ge=1),
) -> RssSourcePageRead:
    return sources_service.list_admin_sources_by_company(
        company_id=company_id,
        limit=limit,
        offset=offset,
        author_id=author_id,
    )


@admin_sources_router.get("/{source_id}", response_model=RssSourceDetailRead)
def read_admin_source_by_id(source_id: int = Path(ge=1)) -> RssSourceDetailRead:
    return sources_service.read_admin_source(source_id=source_id)


@user_sources_router.get("/", response_model=UserSourcePageRead)
def read_user_sources(
    limit: int = Query(default=24, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> UserSourcePageRead:
    return sources_service.list_user_sources(limit=limit, offset=offset)


@user_sources_router.get("/{source_id}/similar", response_model=SimilarSourcesRead)
def read_user_source_similar(
    source_id: int = Path(ge=1),
    limit: int = Query(default=10, ge=1, le=20),
    worker_version: str | None = Query(default=None, min_length=1, max_length=80),
) -> SimilarSourcesRead:
    return sources_service.read_similar_sources(
        source_id=source_id,
        limit=limit,
        worker_version=worker_version,
    )


@user_sources_router.get("/{source_id}", response_model=UserSourceDetailRead)
def read_user_source_by_id(source_id: int = Path(ge=1)) -> UserSourceDetailRead:
    return sources_service.read_user_source(source_id=source_id)
