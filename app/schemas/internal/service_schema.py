from shared_backend.schemas.internal.service_schema import (
    InternalResolvedSessionRead,
    InternalServiceHealthRead,
)

from pydantic import BaseModel, Field


class InternalServiceReadyDependencyRead(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    kind: str = Field(min_length=1, max_length=40)
    status: str = Field(min_length=1, max_length=32)
    detail: str | None = Field(default=None, max_length=512)
    latency_ms: int | None = Field(default=None, ge=0)


class InternalServiceReadyRead(BaseModel):
    service: str = Field(min_length=1, max_length=80)
    status: str = Field(min_length=1, max_length=32)
    dependencies: dict[str, InternalServiceReadyDependencyRead] = Field(default_factory=dict)
