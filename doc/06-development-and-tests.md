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
	manifeed-public-api
```

## Tests

Run all tests:

```bash
pytest -q
```

Current test coverage:

- Python source syntax validation

Recommended next tests:

- route-level tests for auth cookie behavior
- CSRF middleware tests
- dependency tests for admin and API-access guards
- upstream client contract tests with mocked responses
- worker release URL rewrite tests
