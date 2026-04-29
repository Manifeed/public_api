from app.clients.networking.admin_service_networking_client import get_required_admin_service_client
from app.schemas.analytics.analysis_schema import AnalysisOverviewRead, SimilarSourcesRead
from app.schemas.health import HealthRead


def read_health() -> HealthRead:
    return get_required_admin_service_client().read_health()


def read_analysis_overview() -> AnalysisOverviewRead:
    return get_required_admin_service_client().read_analysis_overview()


def read_similar_sources(
    *,
    source_id: int,
    limit: int,
    worker_version: str | None,
) -> SimilarSourcesRead:
    return get_required_admin_service_client().read_similar_sources(
        source_id=source_id,
        limit=limit,
        worker_version=worker_version,
    )
