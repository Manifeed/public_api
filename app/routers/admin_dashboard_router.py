from fastapi import APIRouter, Depends

from app.dependencies.auth_dependencies import require_masked_admin_user
from app.services import admin_dashboard_service

from shared_backend.schemas.health import HealthRead


admin_health_router = APIRouter(
    prefix="/api/admin/health",
    tags=["health"],
    dependencies=[Depends(require_masked_admin_user)],
)


@admin_health_router.get("/", response_model=HealthRead)
def read_admin_health() -> HealthRead:
    return admin_dashboard_service.read_health()
