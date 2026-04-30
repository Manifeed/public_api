from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.routers import auth_router
from app.services import auth_service

from shared_backend.schemas.auth.auth_schema import AuthLogoutRead, AuthRegisterRead, AuthSessionRead
from shared_backend.schemas.auth.session_schema import AuthLoginResult

from .conftest import client_context, override_authenticated_user


def test_register_applies_ip_email_and_pseudo_rate_limits(
    app_env,
    monkeypatch,
    sample_auth_user,
) -> None:
    calls: list[tuple[str, str | None]] = []

    def fake_enforce_rate_limit(request, *, namespace, limit, window_seconds, identifier=None):
        calls.append((namespace, identifier))

    monkeypatch.setattr(auth_router, "enforce_rate_limit", fake_enforce_rate_limit)
    monkeypatch.setattr(
        auth_service,
        "register_auth_user",
        lambda payload: AuthRegisterRead(user=sample_auth_user),
    )

    with client_context() as client:
        response = client.post(
            "/api/auth/register",
            json={
                "email": "User@Example.com",
                "pseudo": "MyPseudo",
                "password": "super-secure-password",
            },
            headers={"origin": "http://frontend.test"},
        )

    assert response.status_code == 200
    assert calls == [
        ("auth-register-ip", None),
        ("auth-register-email", "user@example.com"),
        ("auth-register-pseudo", "mypseudo"),
    ]


def test_login_sets_session_cookie(app_env, monkeypatch, sample_auth_user) -> None:
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    monkeypatch.setattr(
        auth_service,
        "login_auth_user",
        lambda payload: AuthLoginResult(
            session_token="session-token",
            expires_at=expires_at,
            user=sample_auth_user,
        ),
    )

    with client_context() as client:
        response = client.post(
            "/api/auth/login",
            json={"email": "user@example.com", "password": "super-secure-password"},
            headers={"origin": "http://frontend.test"},
        )

    assert response.status_code == 200
    assert response.cookies.get("manifeed_session") == "session-token"


def test_logout_calls_upstream_and_clears_cookie(
    app_env,
    monkeypatch,
    authenticated_user,
) -> None:
    seen: dict[str, str] = {}
    monkeypatch.setattr(
        auth_service,
        "logout_auth_user",
        lambda *, session_token: _record_logout(seen, session_token),
    )

    with client_context() as client:
        override_authenticated_user(client.app, authenticated_user)
        client.cookies.set("manifeed_session", "session-token")
        response = client.post("/api/auth/logout", headers={"origin": "http://frontend.test"})

    assert response.status_code == 200
    assert seen["session_token"] == "session-token"
    assert "manifeed_session=" in response.headers["set-cookie"]
    assert "Max-Age=0" in response.headers["set-cookie"]


def test_session_reads_cookie_and_relays_payload(
    app_env,
    monkeypatch,
    authenticated_user,
    sample_auth_user,
) -> None:
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    seen: dict[str, str] = {}

    def fake_read_auth_session(*, session_token: str) -> AuthSessionRead:
        seen["session_token"] = session_token
        return AuthSessionRead(expires_at=expires_at, user=sample_auth_user)

    monkeypatch.setattr(auth_service, "read_auth_session", fake_read_auth_session)

    with client_context() as client:
        override_authenticated_user(client.app, authenticated_user)
        client.cookies.set("manifeed_session", "session-token")
        response = client.get("/api/auth/session")

    assert response.status_code == 200
    assert seen["session_token"] == "session-token"
    assert response.json()["user"]["email"] == "user@example.com"


def test_csrf_blocks_unsafe_auth_request_without_origin(app_env) -> None:
    with client_context() as client:
        response = client.post(
            "/api/auth/login",
            json={"email": "user@example.com", "password": "super-secure-password"},
        )

    assert response.status_code == 403


def _record_logout(seen: dict[str, str], session_token: str) -> AuthLogoutRead:
    seen["session_token"] = session_token
    return AuthLogoutRead(ok=True)
