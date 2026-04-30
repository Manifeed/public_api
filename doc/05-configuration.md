# Configuration

## Core Runtime

- `APP_ENV`
	- primary environment selector

- `ENVIRONMENT`
	- fallback environment selector

- `NODE_ENV`
	- additional environment selector used by helpers

- `INTERNAL_SERVICE_TOKEN`
	- shared token sent to upstream internal services when configured

- `REQUIRE_INTERNAL_SERVICE_TOKEN`
	- forces strict token expectations in token-validation helpers
	- takes precedence over local/dev environment relaxation

## Browser and Security Settings

- `CORS_ORIGINS`
	- comma-separated allowed origins
	- `*` is rejected when credentials are enabled
	- in development, defaults to `http://localhost:8080,http://localhost:3000`

- `CSRF_TRUSTED_ORIGINS`
	- comma-separated trusted origins for CSRF checks

- `CSRF_TRUST_SELF_ORIGIN`
	- explicitly trust or reject the request's own origin outside production-like environments

- `AUTH_SESSION_COOKIE_SECURE`
	- overrides secure-cookie behavior
	- truthy values force `Secure=true`
	- falsy values force `Secure=false`

## Upstream Service URLs

- `AUTH_SERVICE_URL`
- `USER_SERVICE_URL`
- `ADMIN_SERVICE_URL`
- `CONTENT_SERVICE_URL`
- `WORKER_SERVICE_URL`

If a required upstream URL is missing, the corresponding client raises an
upstream service configuration error when used, and `GET /internal/ready`
reports the dependency as `not_ready` and returns `503`.

## Upstream Timeout Variables

- `AUTH_SERVICE_TIMEOUT_SECONDS` (default: `5.0`)
- `USER_SERVICE_TIMEOUT_SECONDS` (default: `5.0`)
- `ADMIN_SERVICE_TIMEOUT_SECONDS` (default: `10.0`)
- `CONTENT_SERVICE_TIMEOUT_SECONDS` (default: `10.0`)
- `WORKER_SERVICE_TIMEOUT_SECONDS` (default: `10.0`)

Invalid or non-positive timeout values fall back to the default.

## Rate Limiting Variables

- `RATE_LIMIT_ENABLED`
	- enabled by default
	- disable with `0`, `false`, `no`, `off`

- `RATE_LIMIT_REDIS_REQUIRED`
	- explicit strict/optional Redis policy
	- if unset, production-like environments default to strict behavior

- `REDIS_URL`
	- default: `redis://redis:6379/0`

- `REDIS_SOCKET_TIMEOUT_SECONDS`
	- default: `0.2`
	- invalid or non-positive values fall back to default

## Readiness and Operations

- `GET /internal/health`
	- static liveness endpoint

- `GET /internal/ready`
	- validates config and pings critical dependencies
	- returns `200` only when overall readiness is `ready`
	- returns `503` when any critical dependency or strict security check is `not_ready`

- `HEALTH_INCLUDE_DETAILS`
	- not used by `public_api`
	- health and readiness detail payloads stay minimal and dependency-oriented
