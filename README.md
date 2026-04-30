# Manifeed Public API

`public_api` is the public-facing FastAPI gateway for Manifeed.
It exposes browser-facing and client-facing HTTP routes, manages session
cookies, applies CSRF and rate-limit protections, and forwards business
workflows to internal backend services.

This service does not own core business data. Its primary role is to provide a
stable public API surface and orchestrate calls to upstream services.

## What This Service Provides

- Public authentication routes for register, login, logout, and session read
- Session cookie management for browser clients
- Account routes backed by `user_service`
- Admin routes backed by `admin_service`
- Source and RSS read routes backed by `content_service`
- Worker desktop release catalog route backed by `worker_service`
- Readiness endpoint for production orchestration
- Public concerns only: CORS, CSRF, upstream error mapping, and rate limiting

## Architecture Overview

- `app/main.py`: FastAPI app factory, CORS, middleware, router wiring
- `app/routers`: public and admin HTTP route layer
- `app/dependencies`: authenticated/admin access guards
- `app/services`: thin orchestration layer over internal clients
- `app/clients/networking`: upstream HTTP clients and Redis rate-limit client
- `app/middleware`: CSRF and rate limiting
- `app/utils`: environment helpers and session cookie helpers
- `shared_backend`: shared schemas, domain models, error contracts, inter-service auth helpers, and HTTP client primitives

## Upstream Service Dependencies

`public_api` depends on the following internal services:

- `AUTH_SERVICE_URL`
- `USER_SERVICE_URL`
- `ADMIN_SERVICE_URL`
- `CONTENT_SERVICE_URL`
- `WORKER_SERVICE_URL`

All upstream HTTP calls are made with the internal service header
`x-manifeed-internal-token` when `INTERNAL_SERVICE_TOKEN` is configured.

## Quick Start (Local Development)

### 1) Install dependencies

```bash
python3 -m pip install -r requirements.txt
```

### 2) Set a minimal local environment

```bash
export APP_ENV=local
export AUTH_SERVICE_URL=http://localhost:8001
export USER_SERVICE_URL=http://localhost:8002
export ADMIN_SERVICE_URL=http://localhost:8003
export CONTENT_SERVICE_URL=http://localhost:8004
export WORKER_SERVICE_URL=http://localhost:8005
```

Optional settings for browser development:

```bash
export CORS_ORIGINS=http://localhost:3000,http://localhost:8080
export CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://localhost:8080
export REDIS_URL=redis://localhost:6379/0
```

### 3) Run the API

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Main entry points include:

- `GET /internal/health`
- `GET /internal/ready`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/session`
- `GET /api/account/me`
- `GET /api/admin/users`
- `GET /api/sources`
- `GET /api/rss/img/{icon_url}`
- `GET /workers/api/releases/desktop`

## Security Model

- Browser sessions are stored in an `HttpOnly` cookie named
  `manifeed_session`.
- CSRF origin checks are applied to unsafe methods under `/api/`.
- Sensitive routes resolve the current user through `auth_service`.
- Admin routes are guarded by admin-only dependencies.
- Selected routes are rate-limited with Redis-backed counters or in-memory
  fallback in non-strict environments.
- Upstream internal requests can include `x-manifeed-internal-token`.
- Password changes clear the browser cookie while `user_service` revokes
  active server-side sessions.

## Configuration

### Core runtime

- `APP_ENV` / `ENVIRONMENT` / `NODE_ENV`
- `CORS_ORIGINS`
- `CSRF_TRUSTED_ORIGINS`
- `CSRF_TRUST_SELF_ORIGIN`
- `AUTH_SESSION_COOKIE_SECURE`
- `INTERNAL_SERVICE_TOKEN`
- `REQUIRE_INTERNAL_SERVICE_TOKEN`

### Upstream service URLs

- `AUTH_SERVICE_URL`
- `USER_SERVICE_URL`
- `ADMIN_SERVICE_URL`
- `CONTENT_SERVICE_URL`
- `WORKER_SERVICE_URL`

### Upstream service timeouts

- `AUTH_SERVICE_TIMEOUT_SECONDS`
- `USER_SERVICE_TIMEOUT_SECONDS`
- `ADMIN_SERVICE_TIMEOUT_SECONDS`
- `CONTENT_SERVICE_TIMEOUT_SECONDS`
- `WORKER_SERVICE_TIMEOUT_SECONDS`

### Rate limiting

- `RATE_LIMIT_ENABLED`
- `RATE_LIMIT_REDIS_REQUIRED`
- `REDIS_URL`
- `REDIS_SOCKET_TIMEOUT_SECONDS`

## Tests

Run the test suite:

```bash
python -m pytest -q
```

Coverage includes gateway route tests for auth/session flows, CSRF, masked
admin access, RSS and sources routes, jobs and admin dashboard routes, worker
release URL rewriting, readiness, and rate-limit/security behavior.

## Docker

Build from the monorepo root:

```bash
docker build -t manifeed-public-api -f public_api/Dockerfile .
```

Run:

```bash
docker run --rm -p 8000:8000 \
	-e APP_ENV=production \
	-e AUTH_SERVICE_URL='http://auth-service:8000' \
	-e USER_SERVICE_URL='http://user-service:8000' \
	-e ADMIN_SERVICE_URL='http://admin-service:8000' \
	-e CONTENT_SERVICE_URL='http://content-service:8000' \
	-e WORKER_SERVICE_URL='http://worker-service:8000' \
	-e INTERNAL_SERVICE_TOKEN='replace-with-strong-secret-min-32-chars' \
	-e CORS_ORIGINS='https://app.example.com' \
	-e CSRF_TRUSTED_ORIGINS='https://app.example.com' \
	manifeed-public-api
```

The runtime image is multi-stage, runs as a dedicated non-root user, and uses
`/internal/ready` for its container healthcheck. `shared_backend` is installed
from a wheel built locally from the monorepo. The endpoint returns `200`
only when the service is actually ready, and `503` when a critical dependency
or configuration check fails.

## Edge Deployment Notes

- `/api/*` is served by `public_api` through Nginx.
- `/workers/api/*` is served directly by `worker_service` through Nginx.
- `GET /workers/api/releases/desktop` returns edge-routable `download_url`
  values, but the binary download itself is not served by `public_api`.
- `release_notes_url` is preserved from `worker_service`; `public_api` does not
  fabricate a `/workers` page.

## Detailed Documentation

Documentation is available in:

- `doc/README.md`
