from __future__ import annotations

from contextlib import asynccontextmanager
import os
from typing import List, Tuple

from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware

from app.clients.networking.redis_networking_client import reset_redis_client
from app.clients.networking.service_client_registry import (
    close_service_http_client_registry,
    initialize_service_http_client_registry,
)
from shared_backend.errors.exception_handlers import register_exception_handlers
from app.middleware.csrf_middleware import csrf_origin_middleware
from app.middleware.observability_middleware import observability_middleware
from app.routers.account_router import account_router
from app.routers.admin_dashboard_router import admin_analysis_router, admin_health_router
from app.routers.admin_router import admin_router
from app.routers.auth_router import auth_router
from app.routers.jobs_router import jobs_router
from app.routers.rss_router import rss_admin_router, rss_public_router
from app.routers.sources_router import admin_sources_router, user_sources_router
from app.routers.worker_release_router import worker_release_router
from shared_backend.schemas.internal.service_schema import InternalServiceHealthRead
from app.schemas.internal.service_schema import InternalServiceReadyRead
from app.services.readiness_service import read_internal_ready
from app.utils.environment_utils import is_development_environment


def _parse_cors_origins() -> Tuple[List[str], bool]:
    raw_origins = os.getenv("CORS_ORIGINS", "")
    origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    if "*" in origins:
        raise RuntimeError("CORS_ORIGINS cannot contain '*' when credentials are enabled")
    if origins:
        return origins, True
    if is_development_environment():
        return ["http://localhost:8080", "http://localhost:3000"], True
    return [], False


@asynccontextmanager
async def _app_lifespan(_app: FastAPI):
    initialize_service_http_client_registry()
    try:
        yield
    finally:
        close_service_http_client_registry()
        reset_redis_client()


def create_app() -> FastAPI:
    app = FastAPI(title="Manifeed Public API", lifespan=_app_lifespan)
    cors_origins, allow_credentials = _parse_cors_origins()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=allow_credentials,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.middleware("http")(observability_middleware)
    app.middleware("http")(csrf_origin_middleware)

    app.include_router(auth_router)
    app.include_router(account_router)
    app.include_router(admin_router)
    app.include_router(admin_health_router)
    app.include_router(admin_analysis_router)
    app.include_router(jobs_router)
    app.include_router(rss_admin_router)
    app.include_router(rss_public_router)
    app.include_router(admin_sources_router)
    app.include_router(user_sources_router)
    app.include_router(worker_release_router)

    @app.get("/internal/health", response_model=InternalServiceHealthRead)
    def read_internal_health() -> InternalServiceHealthRead:
        return InternalServiceHealthRead(service="public-api", status="ok")

    @app.get("/internal/ready", response_model=InternalServiceReadyRead)
    def read_ready(response: Response) -> InternalServiceReadyRead:
        readiness = read_internal_ready()
        if readiness.status != "ready":
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return readiness

    register_exception_handlers(app)
    return app


app = create_app()
