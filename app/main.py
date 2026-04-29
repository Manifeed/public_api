from __future__ import annotations

import os
from typing import List, Tuple

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.errors.exception_handlers import register_exception_handlers
from app.middleware.csrf_middleware import csrf_origin_middleware
from app.routers.account_router import account_router
from app.routers.admin_dashboard_router import admin_analysis_router, admin_health_router
from app.routers.admin_router import admin_router
from app.routers.auth_router import auth_router
from app.routers.jobs_router import jobs_router
from app.routers.rss_router import rss_admin_router, rss_public_router
from app.routers.sources_router import admin_sources_router, user_sources_router
from app.routers.worker_release_router import worker_release_router
from app.schemas.internal.service_schema import InternalServiceHealthRead
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


def create_app() -> FastAPI:
    app = FastAPI(title="Manifeed Public API")
    cors_origins, allow_credentials = _parse_cors_origins()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=allow_credentials,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
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

    register_exception_handlers(app)
    return app


app = create_app()
