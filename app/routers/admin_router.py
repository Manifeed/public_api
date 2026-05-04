from fastapi import APIRouter, Depends, Path, Query

from app.dependencies.auth_dependencies import require_masked_admin_user
from app.services import admin_service

from shared_backend.schemas.admin.admin_stats_schema import AdminStatsRead
from shared_backend.schemas.admin.admin_user_schema import (
    AdminUserListRead,
    AdminUserRead,
    AdminUserUpdateRequestSchema,
)
from shared_backend.schemas.auth.auth_schema import UserRole

admin_router = APIRouter(prefix="/api/admin", tags=["admin"])


@admin_router.get("/users", response_model=AdminUserListRead)
def read_admin_users_route(
    role: UserRole | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    api_access_enabled: bool | None = Query(default=None),
    search: str | None = Query(default=None, min_length=1, max_length=320),
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user=Depends(require_masked_admin_user),
) -> AdminUserListRead:
    return admin_service.read_admin_users(
        current_user=current_user,
        role=role,
        is_active=is_active,
        api_access_enabled=api_access_enabled,
        search=search,
        limit=limit,
        offset=offset,
    )


@admin_router.patch("/users/{user_id}", response_model=AdminUserRead)
def update_admin_user_route(
    payload: AdminUserUpdateRequestSchema,
    user_id: int = Path(ge=1),
    current_user=Depends(require_masked_admin_user),
) -> AdminUserRead:
    return admin_service.update_admin_user(
        current_user=current_user,
        user_id=user_id,
        payload=payload,
    )


@admin_router.get("/stats", response_model=AdminStatsRead)
def read_admin_stats_route(
    _current_user=Depends(require_masked_admin_user),
) -> AdminStatsRead:
    return admin_service.read_admin_stats()
