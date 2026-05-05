# Security

## Session Cookie Security

Session cookie settings:

- cookie name: `manifeed_session`
- `HttpOnly`: enabled
- `SameSite`: `Lax`
- `Secure`: inferred from `X-Forwarded-Proto=https`, normally set by Traefik
- path: `/`

The session token is read from the cookie, not from a public bearer header.
Password changes clear the browser cookie in `public_api`, while `user_service`
revokes active server-side sessions.

## CSRF Protection

CSRF checks are applied by `csrf_origin_middleware`.

Policy:

- only unsafe methods are checked: `POST`, `PUT`, `PATCH`, `DELETE`
- only `/api/*` routes are checked
- request origin is taken from `Origin`, then `Referer`
- trusted origins come from configuration and environment-aware fallbacks

Trusted-origin behavior:

- `CSRF_TRUSTED_ORIGINS` is the primary allow-list
- in development, `CORS_ORIGINS` can seed the trusted-origin set
- non-production-like environments may trust the request's own origin

## Authentication and Authorization

Current-user resolution:

- authenticated routes call `auth_service` to resolve the current session
- account routes forward that resolved context to `user_service` instead of sending the raw session token again
- admin routes require `role == "admin"`
- API key routes require `api_access_enabled == true`

Masked access behavior:

- some guards intentionally return `NotFound` instead of `Forbidden`
- this reduces route discoverability for unauthorized callers

## Inter-Service Security

Outbound internal-service header:

- `x-manifeed-internal-token`

Behavior:

- the service fails startup if no strong internal token is configured
- the header is added to upstream HTTP calls from the configured token
- token comparison logic comes from `shared_backend/security/internal_service_auth.py`

## Traefik and Edge Trust

Production traffic is expected to flow through:

`Client -> Traefik HTTPS/domain -> nginx HTTP interne -> public_api -> services internes`

Traefik owns TLS termination, HTTP-to-HTTPS redirects, domain routing, and
normalization of `X-Forwarded-*` headers. Nginx is not exposed publicly by the
default compose stack and relays the trusted forwarded headers to `public_api`.

## Rate Limiting Security

Protected flows:

- auth register
- auth login
- account password update
- account API key creation

Gateway rate limits are identifier-based:

- register: email + pseudo
- login: email
- account password: user ID
- account API key creation: user ID

Redis availability policy:

- strict mode can fail closed when Redis is unavailable
- optional mode falls back to in-memory counters

## Upstream Error Handling

Upstream HTTP failures are normalized into application errors.

Behavior:

- transport-level failures become upstream-service errors
- JSON upstream error payloads are mapped into application-level responses
- this gives callers a more consistent public error surface
- structured request logs capture `request_id`, route template, upstream target, latency, and failure class
