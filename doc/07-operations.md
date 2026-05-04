# Operations

## Production Recommendations

- set `APP_ENV=production` or an explicit production-like value
- configure all required upstream URLs explicitly
- configure `CORS_ORIGINS` and `CSRF_TRUSTED_ORIGINS` for the real frontend origins
- configure `PUBLIC_BASE_URL` to the real edge origin used for public worker release URLs
- configure a strong `INTERNAL_SERVICE_TOKEN` for internal upstream calls
- keep `RATE_LIMIT_REDIS_REQUIRED=true` in production environments
- route edge traffic only after `GET /internal/ready` returns `200`
- keep `AUTH_SESSION_COOKIE_SECURE=true` behind TLS termination
- monitor upstream latency and failure rates per internal service
- let Nginx own coarse IP throttling and keep gateway limits scoped to business identifiers
- ingest structured gateway logs with `request_id`, route template, upstream target, status, and latency

## Edge Contract

- `/api/*` is served by `public_api` through Nginx
- `/workers/api/*` is served directly by `worker_service` through Nginx
- `public_api` still exposes `GET /workers/api/releases/desktop`, but release binaries are downloaded from the edge route backed by `worker_service`
- proxy headers `X-Forwarded-*` are part of the trusted deployment model for CSRF/self-origin logic and secure cookie behavior

## Known Constraints

- public behavior depends directly on upstream service availability
- readiness depends on the availability of the internal upstream `/internal/health` endpoints
- readiness returns `503` when a critical dependency or strict config check is not ready
- optional rate-limit mode can still fall back to in-memory counters outside strict production settings

## Documentation Maintenance

Update docs in this folder whenever behavior changes in:

- `app/main.py`
- `app/routers/*`
- `app/dependencies/auth_dependencies.py`
- `app/services/*`
- `app/clients/networking/*`
- `app/middleware/*`
- `app/utils/session_cookie.py`
