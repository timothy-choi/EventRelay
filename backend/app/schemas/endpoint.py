from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class EndpointCreate(BaseModel):
    name: str
    target_url: HttpUrl
    simulation_latency_ms: int = Field(default=0, ge=0)
    simulation_failure_rate: int = Field(default=0, ge=0, le=100)
    simulation_timeout_rate: int = Field(default=0, ge=0, le=100)


class EndpointRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    target_url: str
    is_active: bool
    simulation_latency_ms: int
    simulation_failure_rate: int
    simulation_timeout_rate: int
    created_at: datetime


class EndpointUpdate(BaseModel):
    is_active: Optional[bool] = None
    simulation_latency_ms: Optional[int] = Field(default=None, ge=0)
    simulation_failure_rate: Optional[int] = Field(default=None, ge=0, le=100)
    simulation_timeout_rate: Optional[int] = Field(default=None, ge=0, le=100)


class EndpointStatsRead(BaseModel):
    endpoint_id: uuid.UUID
    endpoint_name: str
    total_deliveries: int
    succeeded: int
    failed: int
    retrying: int
    pending: int
    success_rate: float
    avg_latency_ms: float | None
    p95_latency_ms: int | None
    total_attempts: int
    timeout_count: int
    connection_error_count: int
    http_4xx_count: int
    http_5xx_count: int
