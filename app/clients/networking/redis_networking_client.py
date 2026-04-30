from __future__ import annotations

from dataclasses import dataclass
import os

from redis import Redis
from redis.exceptions import RedisError


DEFAULT_REDIS_URL = "redis://redis:6379/0"
DEFAULT_REDIS_TIMEOUT_SECONDS = 0.2
_INCREMENT_WITH_TTL_SCRIPT = """
local value = redis.call("INCR", KEYS[1])
if value == 1 then
  redis.call("EXPIRE", KEYS[1], ARGV[1])
end
return value
"""


class RedisCommandError(RuntimeError):
    """Raised when Redis cannot execute a command."""


@dataclass(frozen=True)
class RedisConnectionConfig:
    url: str
    timeout_seconds: float


_redis_client: Redis | None = None


class RedisNetworkingClient:
    def __init__(
        self,
        config: RedisConnectionConfig | None = None,
        redis_client: Redis | None = None,
    ) -> None:
        self.config = config or RedisConnectionConfig(
            url=_resolve_redis_url(),
            timeout_seconds=_resolve_redis_timeout_seconds(),
        )
        self._redis_client = redis_client or get_redis_client(self.config)

    def ping(self) -> str:
        try:
            return self._redis_client.ping() and "PONG" or "PONG"
        except RedisError as exception:
            raise RedisCommandError(str(exception)) from exception

    def increment_with_ttl(self, key: str, ttl_seconds: int) -> int:
        if ttl_seconds <= 0:
            raise RedisCommandError("Redis TTL must be positive")
        try:
            result = self._redis_client.eval(_INCREMENT_WITH_TTL_SCRIPT, 1, key, ttl_seconds)
        except RedisError as exception:
            raise RedisCommandError(str(exception)) from exception
        return int(result)


def get_redis_client(config: RedisConnectionConfig | None = None) -> Redis:
    global _redis_client
    if config is not None:
        return _build_redis_client(config)
    if _redis_client is None:
        _redis_client = _build_redis_client(
            RedisConnectionConfig(
                url=_resolve_redis_url(),
                timeout_seconds=_resolve_redis_timeout_seconds(),
            )
        )
    return _redis_client


def reset_redis_client() -> None:
    global _redis_client
    if _redis_client is not None:
        _redis_client.close()
        _redis_client = None


def _build_redis_client(config: RedisConnectionConfig) -> Redis:
    return Redis.from_url(
        config.url,
        socket_timeout=config.timeout_seconds,
        socket_connect_timeout=config.timeout_seconds,
        decode_responses=True,
    )


def _resolve_redis_url() -> str:
    return os.getenv("REDIS_URL", DEFAULT_REDIS_URL).strip() or DEFAULT_REDIS_URL


def _resolve_redis_timeout_seconds() -> float:
    raw_value = os.getenv("REDIS_SOCKET_TIMEOUT_SECONDS", str(DEFAULT_REDIS_TIMEOUT_SECONDS))
    try:
        timeout_seconds = float(raw_value)
    except ValueError:
        return DEFAULT_REDIS_TIMEOUT_SECONDS
    if timeout_seconds <= 0:
        return DEFAULT_REDIS_TIMEOUT_SECONDS
    return timeout_seconds
