# Overview

## Service Purpose

`public_api` is the public gateway for Manifeed.
It exposes browser-facing and client-facing HTTP routes while delegating core
business operations to internal backend services.

This service is responsible for request entry, cookie/session handling, public
security controls, and upstream orchestration.

## Responsibilities

- Expose public auth routes for registration, login, logout, and session read
- Resolve current-user context through `auth_service`
- Forward account workflows to `user_service` with the resolved current-user context
- Forward admin workflows to `admin_service`
- Forward source and RSS read flows to `content_service`
- Forward worker desktop release catalog reads to `worker_service`
- Apply CORS, CSRF, rate limiting, and upstream error mapping

## Technical Stack

- FastAPI
- httpx
- Redis-compatible counters for rate limiting
- `manifeed-shared-backend` for shared schemas/domain/errors
