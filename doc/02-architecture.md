# Architecture

## High-Level Layers

- `app/main.py`: FastAPI app creation, CORS, middleware registration, router mounting
- `app/routers`: HTTP route definitions for public and admin surfaces
- `app/dependencies`: current-user, admin, and API-access guards
- `app/services`: thin business-facing orchestration layer
- `app/clients/networking`: upstream HTTP clients and Redis client
- `app/middleware`: CSRF and rate-limit enforcement
- `app/utils`: environment and session-cookie helpers

## Route Layer

Mounted routers:

- `auth_router` -> `/api/auth`
- `account_router` -> `/api/account`
- `admin_router` -> `/api/admin`
- `admin_health_router` -> `/api/admin/health`
- `admin_analysis_router` -> `/api/admin/analysis`
- `jobs_router` -> `/api/admin/jobs`
- `rss_admin_router` -> `/api/admin/rss`
- `rss_public_router` -> `/api/rss`
- `admin_sources_router` -> `/api/admin/sources`
- `user_sources_router` -> `/api/sources`
- `worker_release_router` -> `/workers/api`

Health route:

- `GET /internal/health`

## Dependency Layer

Authentication and authorization dependencies live in
`app/dependencies/auth_dependencies.py`.

Core guards:

- `require_authenticated_user`
- `require_admin_user`
- `require_api_enabled_user`
- `require_masked_admin_user`
- `require_masked_api_enabled_user`

These dependencies resolve the current session through `auth_service` and apply
role or feature-access checks before route handlers execute.

## Service Layer

Service modules are intentionally thin and forward calls to upstream clients:

- `auth_service.py`
- `account_service.py`
- `admin_service.py`
- `admin_dashboard_service.py`
- `jobs_service.py`
- `rss_service.py`
- `sources_service.py`
- `worker_release_service.py`

## Networking Layer

Upstream clients:

- `auth_service_networking_client.py`
- `user_service_networking_client.py`
- `admin_service_networking_client.py`
- `content_service_networking_client.py`
- `worker_service_networking_client.py`

Shared transport logic:

- `service_http_client.py`

Rate-limit backend client:

- `redis_networking_client.py`

## Error and Schema Strategy

- Shared exceptions and handlers come from `shared_backend`
- Public contracts are modeled with Pydantic schemas under `app/schemas`
- Upstream HTTP errors are mapped into application errors in one shared place
