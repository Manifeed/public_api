from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.services import auth_service
from app.services import auth_session_context
from app.services import auth_upstream
from shared_backend.domain.current_user import AuthenticatedUserContext


class _FakeAuthClient:
    def __init__(self) -> None:
        self.resolve_calls = 0
        self.logout_calls = 0

    def resolve_session(self, *, session_token: str):
        self.resolve_calls += 1
        now = datetime.now(timezone.utc)
        return type(
            "ResolvedSession",
            (),
            {
                "user_id": 7,
                "email": "cache@example.com",
                "role": "admin",
                "is_active": True,
                "api_access_enabled": True,
                "session_expires_at": now + timedelta(minutes=10),
            },
        )()

    def logout(self, *, session_token: str):
        self.logout_calls += 1
        return type("LogoutResponse", (), {"ok": True})()


class _FakeRedisClient:
    def __init__(self) -> None:
        self.data: dict[str, dict[str, object]] = {}
        self.deleted: set[str] = set()

    def get_json(self, key: str) -> dict[str, object] | None:
        return self.data.get(key)

    def set_json_with_ttl(self, key: str, value: dict[str, object], ttl_seconds: int) -> None:
        self.data[key] = value

    def delete_key(self, key: str) -> None:
        self.deleted.add(key)
        self.data.pop(key, None)


def test_resolve_authenticated_user_uses_cache_hit(monkeypatch) -> None:
    now = datetime.now(timezone.utc)
    fake_auth_client = _FakeAuthClient()
    fake_redis = _FakeRedisClient()
    cache_key = auth_session_context._build_auth_context_cache_key(session_token="msess_cache")
    fake_redis.data[cache_key] = {
        "user_id": 5,
        "email": "cached@example.com",
        "role": "user",
        "is_active": True,
        "api_access_enabled": False,
        "session_expires_at": (now + timedelta(minutes=3)).isoformat(),
    }
    monkeypatch.setattr(auth_session_context, "get_required_auth_service_client", lambda: fake_auth_client)
    monkeypatch.setattr(auth_session_context, "RedisNetworkingClient", lambda: fake_redis)

    resolved_user = auth_service.resolve_authenticated_user(session_token="msess_cache")

    assert isinstance(resolved_user, AuthenticatedUserContext)
    assert resolved_user.user_id == 5
    assert fake_auth_client.resolve_calls == 0


def test_resolve_authenticated_user_sets_cache_on_miss(monkeypatch) -> None:
    fake_auth_client = _FakeAuthClient()
    fake_redis = _FakeRedisClient()
    monkeypatch.setattr(auth_session_context, "get_required_auth_service_client", lambda: fake_auth_client)
    monkeypatch.setattr(auth_session_context, "RedisNetworkingClient", lambda: fake_redis)

    resolved_user = auth_service.resolve_authenticated_user(session_token="msess_miss")

    assert resolved_user.user_id == 7
    assert fake_auth_client.resolve_calls == 1
    cache_key = auth_session_context._build_auth_context_cache_key(session_token="msess_miss")
    assert cache_key in fake_redis.data


def test_logout_invalidates_auth_context_cache(monkeypatch) -> None:
    fake_auth_client = _FakeAuthClient()
    fake_redis = _FakeRedisClient()
    monkeypatch.setattr(auth_upstream, "get_required_auth_service_client", lambda: fake_auth_client)
    monkeypatch.setattr(auth_session_context, "RedisNetworkingClient", lambda: fake_redis)

    logout_result = auth_service.logout_auth_user(session_token="msess_logout")

    assert logout_result.ok is True
    assert fake_auth_client.logout_calls == 1
    cache_key = auth_session_context._build_auth_context_cache_key(session_token="msess_logout")
    assert cache_key in fake_redis.deleted
