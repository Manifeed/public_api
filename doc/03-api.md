# API Reference

## Health Endpoint

### `GET /internal/health`

Liveness endpoint.

Response:

```json
{
	"service": "public-api",
	"status": "ok"
}
```

## Auth Endpoints

### `POST /api/auth/register`

Creates a user through `auth_service`.

Behavior:

- forwards the payload to `auth_service`
- applies IP-based rate limiting before forwarding

Rate limits:

- IP: 10 requests / 1 hour

### `POST /api/auth/login`

Authenticates a user through `auth_service` and sets the public session cookie.

Behavior:

- applies IP-based and email-based rate limiting
- forwards credentials to `auth_service`
- stores the returned session token in `manifeed_session`
- returns session expiration and user payload, but not the raw session token

Rate limits:

- IP: 30 requests / 5 minutes
- Email: 10 requests / 5 minutes

### `POST /api/auth/logout`

Requires an authenticated session cookie.

Behavior:

- resolves the current user first
- sends the session token to `auth_service/logout`
- clears the public session cookie

Response:

```json
{
	"ok": true
}
```

### `GET /api/auth/session`

Requires an authenticated session cookie.

Behavior:

- resolves the current user first
- returns the session view from `auth_service`

## Account Endpoints

### `GET /api/account/me`

Returns the current account payload from `user_service`.

### `PATCH /api/account/me`

Updates the current account profile through `user_service`.

### `PATCH /api/account/password`

Updates the current account password through `user_service`.

Behavior:

- forwards the password-change request to `user_service`
- clears the browser session cookie after success

### `GET /api/account/api-keys`

Requires authenticated user with `api_access_enabled=true`.

Returns the current user's API keys from `user_service`.

### `POST /api/account/api-keys`

Requires authenticated user with `api_access_enabled=true`.

Behavior:

- forwards API key creation to `user_service`
- rate-limits by current user ID

Rate limits:

- User: 5 requests / 1 hour

### `DELETE /api/account/api-keys/{api_key_id}`

Requires authenticated user with `api_access_enabled=true`.

Deletes an API key through `user_service`.

## Admin Endpoints

All admin routes require admin access through masked admin dependency checks.

### Users

- `GET /api/admin/users`
- `PATCH /api/admin/users/{user_id}`
- `GET /api/admin/stats`

### Health and Analysis

- `GET /api/admin/health/`
- `GET /api/admin/analysis/overview`
- `GET /api/admin/analysis/similar-sources`

### Jobs

- `GET /api/admin/jobs`
- `POST /api/admin/jobs/rss-scrape`
- `POST /api/admin/jobs/source-embedding`
- `GET /api/admin/jobs/automation`
- `PATCH /api/admin/jobs/automation`
- `GET /api/admin/jobs/{job_id}`
- `GET /api/admin/jobs/{job_id}/tasks`

### RSS

- `GET /api/admin/rss/companies`
- `GET /api/admin/rss/`
- `POST /api/admin/rss/sync`
- `PATCH /api/admin/rss/feeds/{feed_id}/enabled`
- `PATCH /api/admin/rss/companies/{company_id}/enabled`

### Sources

- `GET /api/admin/sources/`
- `GET /api/admin/sources/feeds/{feed_id}`
- `GET /api/admin/sources/companies/{company_id}`
- `GET /api/admin/sources/{source_id}`

## Public Content Endpoints

### `GET /api/sources`

Requires an authenticated session cookie.

Returns the user-facing source page from `content_service`.

### `GET /api/sources/{source_id}`

Requires an authenticated session cookie.

Returns the user-facing source detail from `content_service`.

### `GET /api/sources/{source_id}/similar`

Requires an authenticated session cookie.

Returns similar-source analysis from `content_service`.

### `GET /api/rss/img/{icon_url}`

Returns RSS icon/image bytes streamed from `content_service`.

Behavior:

- preserves upstream content type when available
- adds `content-disposition` when upstream filename is present

### `GET /workers/api/releases/desktop`

Returns the public worker desktop release catalog from `worker_service`.

Behavior:

- reads the desktop release list from `worker_service`
- rewrites `download_url` and `release_notes_url` to the current public base URL

## Runtime Flows

### Browser Login Flow

1. apply public rate limits
2. forward credentials to `auth_service`
3. receive session token and expiration
4. set `manifeed_session` cookie
5. return user/session metadata to the caller

### Authenticated Request Flow

1. read `manifeed_session` cookie
2. resolve session through `auth_service`
3. build current-user context
4. apply role or API-access checks
5. call the target upstream service

### Public RSS Image Flow

1. accept public image request
2. fetch the image bytes from `content_service`
3. copy media type and optional filename
4. return the image response to the caller
