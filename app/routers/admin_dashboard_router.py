from fastapi import APIRouter, Depends, Query

from app.dependencies.auth_dependencies import require_masked_admin_user
from app.schemas.analytics.analysis_schema import AnalysisOverviewRead, SimilarSourcesRead
from app.schemas.health import HealthRead
from app.services import admin_dashboard_service


admin_health_router = APIRouter(
    prefix="/api/admin/health",
    tags=["health"],
    dependencies=[Depends(require_masked_admin_user)],
)
admin_analysis_router = APIRouter(
    prefix="/api/admin/analysis",
    tags=["analysis"],
    dependencies=[Depends(require_masked_admin_user)],
)


@admin_health_router.get("/", response_model=HealthRead)
def read_admin_health() -> HealthRead:
    return admin_dashboard_service.read_health()


@admin_analysis_router.get("/overview", response_model=AnalysisOverviewRead)
def read_analysis_overview() -> AnalysisOverviewRead:
    return admin_dashboard_service.read_analysis_overview()


@admin_analysis_router.get("/similar-sources", response_model=SimilarSourcesRead)
def read_similar_sources(
    source_id: int = Query(ge=1),
    limit: int = Query(default=10, ge=1, le=20),
    worker_version: str | None = Query(default=None, min_length=1, max_length=80),
) -> SimilarSourcesRead:
    return admin_dashboard_service.read_similar_sources(
        source_id=source_id,
        limit=limit,
        worker_version=worker_version,
    )
