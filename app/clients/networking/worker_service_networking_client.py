from __future__ import annotations

import httpx

from app.clients.networking.service_client_registry import get_service_http_client_registry
from app.clients.networking.service_http_client import (
    ServiceClientConfig,
    build_service_config,
    request_service,
)
from shared_backend.schemas.internal.service_schema import InternalServiceHealthRead

class WorkerServiceNetworkingClient:
    def __init__(
        self,
        config: ServiceClientConfig,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._config = config
        self._http_client = http_client

    @classmethod
    def from_env(cls) -> "WorkerServiceNetworkingClient | None":
        config = build_service_config(
            base_url_env="WORKER_SERVICE_URL",
            timeout_env="WORKER_SERVICE_TIMEOUT_SECONDS",
            default_timeout_seconds=10.0,
            service_name="Worker",
        )
        if config is None:
            return None
        registry = get_service_http_client_registry()
        return cls(config, http_client=registry.worker if registry is not None else None)

    def read_internal_health(self) -> InternalServiceHealthRead:
        response = request_service(
            config=self._config,
            method="GET",
            path="/internal/health",
            http_client=self._http_client,
        )
        return InternalServiceHealthRead.model_validate(response.json())


def get_worker_service_client() -> WorkerServiceNetworkingClient | None:
    return WorkerServiceNetworkingClient.from_env()
