# Architecture

## High-Level Layers

- `app/main.py`: FastAPI app creation, CORS, middleware registration, router mounting
- `app/routers`: HTTP route definitions for public and admin surfaces
- `app/dependencies`: current-user, admin, and API-access guards
- `app/services`: thin business-facing orchestration layer
- `app/clients/networking`: local upstream HTTP clients, transport helpers, and Redis client
- `app/clients/providers`: adapters that inject local transport/observability into shared clients
- `app/middleware`: CSRF and rate-limit enforcement
- `app/utils`: environment and session-cookie helpers

## Route Layer

Mounted routers:

- `auth_router` -> `/api/auth`
- `account_router` -> `/api/account`
- `admin_router` -> `/api/admin`
- `admin_health_router` -> `/api/admin/health`
- `jobs_router` -> `/api/admin/jobs`
- `rss_admin_router` -> `/api/admin/rss`
- `admin_sources_router` -> `/api/admin/sources`
- `user_sources_router` -> `/api/sources`
- `install_router` -> `/install`

Health routes:

- `GET /internal/health`
- `GET /internal/ready`

## Dependency Layer

Authentication and authorization dependencies live in
`app/dependencies/auth_dependencies.py`.

Core guards:

- `require_authenticated_user`
- `require_masked_admin_user`
- `require_masked_api_enabled_user`

These dependencies resolve the current session through `auth_service` and apply
role or feature-access checks before route handlers execute.

For account routes, `public_api` resolves the session once and forwards the
resulting current-user context to `user_service` over the internal authenticated
service channel. `user_service` does not re-resolve the same session for these
account calls.

## Service Layer

Service modules are intentionally thin and forward calls to upstream clients:

- `auth_service.py`
- `account_service.py`
- `admin_service.py`
- `admin_dashboard_service.py`
- `jobs_service.py`
- `rss_service.py`
- `sources_service.py`

## Client Layer

Provider adapters for shared upstream clients:

- `app/clients/providers/auth_service_client_provider.py`
- `app/clients/providers/user_service_client_provider.py`
- `app/clients/providers/content_service_client_provider.py`

Local networking clients:

- `app/clients/networking/admin_service_networking_client.py`
- `app/clients/networking/worker_service_networking_client.py`

Shared clients wrapped by providers:

- `shared_backend.clients.auth_service_networking_client`
- `shared_backend.clients.user_service_networking_client`
- `shared_backend.clients.content_service_networking_client`

Shared transport logic:

- `service_http_client.py`

Providers inject pooled HTTP clients and upstream-call tracing into clients
implemented in `shared_backend`.

Rate-limit backend client:

- `redis_networking_client.py`

## Error and Schema Strategy

- Shared exceptions and handlers come from `shared_backend`
- Public contracts are modeled with Pydantic schemas under `app/schemas`
- Upstream HTTP errors are mapped into application errors in one shared place
