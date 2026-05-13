from __future__ import annotations

from app.dependencies import auth_dependencies
from app.services import account_service

from shared_backend.schemas.account.account_schema import AccountMeRead, AccountPasswordUpdateRead

from .conftest import client_context, override_authenticated_user


def test_account_me_passes_resolved_current_user_to_user_service(
    app_env,
    monkeypatch,
    authenticated_user,
    sample_auth_user,
) -> None:
    seen: dict[str, object] = {}

    def fake_read_account_me(*, current_user):
        seen["current_user"] = current_user
        return AccountMeRead(user=sample_auth_user)

    monkeypatch.setattr(account_service, "read_account_me", fake_read_account_me)

    with client_context() as client:
        override_authenticated_user(client.app, authenticated_user)
        client.cookies.set("manifeed_session", "session-token")
        response = client.get("/api/account/me")

    assert response.status_code == 200
    assert seen["current_user"] is authenticated_user


def test_account_password_clears_cookie_after_success(
    app_env,
    monkeypatch,
    authenticated_user,
) -> None:
    monkeypatch.setattr(
        account_service,
        "update_account_password",
        lambda *, current_user, payload: AccountPasswordUpdateRead(ok=True),
    )

    with client_context() as client:
        override_authenticated_user(client.app, authenticated_user)
        client.cookies.set("manifeed_session", "session-token")
        response = client.patch(
            "/api/account/password",
            json={
                "current_password": "current-password",
                "new_password": "new-super-secure-password",
            },
            headers={"origin": "http://frontend.test"},
        )

    assert response.status_code == 200
    assert "Max-Age=0" in response.headers["set-cookie"]


def test_admin_route_masks_non_admin_as_not_found(
    app_env,
    monkeypatch,
    authenticated_user,
) -> None:
    monkeypatch.setattr(
        auth_dependencies,
        "resolve_authenticated_user",
        lambda *, session_token: authenticated_user,
    )

    with client_context() as client:
        client.cookies.set("manifeed_session", "session-token")
        response = client.get("/api/admin/users")

    assert response.status_code == 404
