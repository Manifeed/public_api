# Operations

## Production Recommendations

- set `APP_ENV=production` or an explicit production-like value
- configure all required upstream URLs explicitly
- configure `CORS_ORIGINS` and `CSRF_TRUSTED_ORIGINS` for the real frontend origins
- configure a strong `INTERNAL_SERVICE_TOKEN` for internal upstream calls
- keep `RATE_LIMIT_REDIS_REQUIRED=true` in production environments
- monitor upstream latency and failure rates per internal service

## Known Constraints

- health exposure currently provides liveness only through `GET /internal/health`
- public behavior depends directly on upstream service availability
- each upstream request currently creates a fresh `httpx.Client` when no client is injected
- Redis rate-limit increment and TTL are sent as separate commands
- test coverage is currently minimal

## Documentation Maintenance

Update docs in this folder whenever behavior changes in:

- `app/main.py`
- `app/routers/*`
- `app/dependencies/auth_dependencies.py`
- `app/services/*`
- `app/clients/networking/*`
- `app/middleware/*`
- `app/utils/session_cookie.py`
