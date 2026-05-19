# Development and Testing

## Local Setup

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Minimum local environment:

```bash
export APP_ENV=local
export AUTH_SERVICE_URL=http://localhost:8001
export USER_SERVICE_URL=http://localhost:8002
export ADMIN_SERVICE_URL=http://localhost:8003
export CONTENT_SERVICE_URL=http://localhost:8004
export WORKER_SERVICE_URL=http://localhost:8005
export PUBLIC_BASE_URL=http://localhost
export INTERNAL_SERVICE_TOKEN=replace-with-strong-secret-min-32-chars
```

Optional browser-friendly local settings:

```bash
export CORS_ORIGINS=http://localhost:3000,http://localhost:8080
export CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://localhost:8080
export REDIS_URL=redis://localhost:6379/0
```

Run service:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Docker

Build from monorepo root:

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
	-e PUBLIC_BASE_URL='https://app.example.com' \
	manifeed-public-api
```

## Tests

Run all tests from `public_api/`:

```bash
cd public_api
pytest -q
```

`tests/conftest.py` bootstraps the minimum env required for import-time app
creation. Route tests that need upstream URLs or CSRF settings should use the
`app_env` fixture.

Current coverage includes:

- Python syntax validation (`test_source_syntax.py`)
- auth routes, session cookie behavior, and auth-context cache
- account and admin route delegation
- jobs and admin health routes
- RSS and sources routes, including removed search filters
- rate limiting and CSRF/security contracts
- readiness and worker release checks
- admin networking client payload wrapping
- install script route
- documentation and infra contract checks against the monorepo
