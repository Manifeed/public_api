from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx

from app.clients.networking import user_service_networking_client
from app.clients.networking.user_service_networking_client import UserServiceNetworkingClient
from shared_backend.clients.service_http_client import ServiceClientConfig
from shared_backend.schemas.account.account_schema import (
    AccountMeRead,
    UserApiKeyCreateRequestSchema,
    UserApiKeyCreateRead,
    UserApiKeyDeleteRead,
)
from shared_backend.schemas.internal.auth_service_schema import InternalSessionTokenRequest


def _config() -> ServiceClientConfig:
    return ServiceClientConfig(
        base_url="http://user-service:8000",
        internal_token="x" * 32,
        timeout_seconds=5.0,
        service_name="User",
    )


def _session_token() -> str:
    return "msess_example"


def test_read_account_me_wraps_session_token_payload(monkeypatch, sample_auth_user) -> None:
    seen: dict[str, object] = {}

    def fake_request_service(**kwargs) -> httpx.Response:
        seen.update(kwargs)
        return httpx.Response(
            200,
            json={"user": sample_auth_user.model_dump(mode="json")},
            request=httpx.Request("POST", "http://user-service:8000/internal/users/account/me"),
        )

    monkeypatch.setattr(user_service_networking_client, "request_service", fake_request_service)
    client = UserServiceNetworkingClient(_config())
    session_token = _session_token()

    response = client.read_account_me(session_token=session_token)

    assert isinstance(response, AccountMeRead)
    assert seen["path"] == "/internal/users/account/me"
    assert seen["json"] == {
        "payload": InternalSessionTokenRequest(session_token=session_token).model_dump(mode="json")
    }


def test_read_account_api_keys_wraps_session_token_payload(monkeypatch) -> None:
    seen: dict[str, object] = {}

    def fake_request_service(**kwargs) -> httpx.Response:
        seen.update(kwargs)
        return httpx.Response(
            200,
            json={"items": []},
            request=httpx.Request("POST", "http://user-service:8000/internal/users/account/api-keys/list"),
        )

    monkeypatch.setattr(user_service_networking_client, "request_service", fake_request_service)
    client = UserServiceNetworkingClient(_config())
    session_token = _session_token()

    response = client.read_account_api_keys(session_token=session_token)

    assert response.items == []
    assert seen["path"] == "/internal/users/account/api-keys/list"
    assert seen["json"] == {
        "payload": InternalSessionTokenRequest(session_token=session_token).model_dump(mode="json")
    }


def test_create_account_api_key_wraps_internal_request_payload(monkeypatch) -> None:
    seen: dict[str, object] = {}

    def fake_request_service(**kwargs) -> httpx.Response:
        seen.update(kwargs)
        return httpx.Response(
            200,
            json={
                "api_key": "mf_test_key",
                "api_key_info": {
                    "id": 9,
                    "label": "smoke",
                    "worker_type": "rss_scrapper",
                    "worker_name": "user-rss_scrapper-1",
                    "key_prefix": "mf_1234",
                    "last_used_at": None,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            },
            request=httpx.Request("POST", "http://user-service:8000/internal/users/account/api-keys"),
        )

    monkeypatch.setattr(user_service_networking_client, "request_service", fake_request_service)
    client = UserServiceNetworkingClient(_config())
    session_token = _session_token()
    payload = UserApiKeyCreateRequestSchema(label="smoke", worker_type="rss_scrapper")

    response = client.create_account_api_key(session_token=session_token, payload=payload)

    assert isinstance(response, UserApiKeyCreateRead)
    assert seen["path"] == "/internal/users/account/api-keys"
    assert seen["json"] == {
        "payload": {
            "session_token": session_token,
            "payload": payload.model_dump(mode="json"),
        }
    }


def test_delete_account_api_key_wraps_current_user_payload(monkeypatch) -> None:
    seen: dict[str, object] = {}

    def fake_request_service(**kwargs) -> httpx.Response:
        seen.update(kwargs)
        return httpx.Response(
            200,
            json={"ok": True},
            request=httpx.Request(
                "POST",
                "http://user-service:8000/internal/users/account/api-keys/9/delete",
            ),
        )

    monkeypatch.setattr(user_service_networking_client, "request_service", fake_request_service)
    client = UserServiceNetworkingClient(_config())
    session_token = _session_token()

    response = client.delete_account_api_key(session_token=session_token, api_key_id=9)

    assert isinstance(response, UserApiKeyDeleteRead)
    assert seen["path"] == "/internal/users/account/api-keys/9/delete"
    assert seen["json"] == {
        "payload": InternalSessionTokenRequest(session_token=session_token).model_dump(mode="json")
    }
