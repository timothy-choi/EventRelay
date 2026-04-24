from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class DeliveryAttemptRead(BaseModel):
    id: uuid.UUID
    attempt_number: int
    status: str
    response_code: int | None
    latency_ms: int | None
    failure_type: str | None
    error_message: str | None
    started_at: datetime
    completed_at: datetime | None


class DeliveryListItem(BaseModel):
    id: uuid.UUID
    status: str
    total_attempts: int
    next_retry_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime
    endpoint_id: uuid.UUID
    endpoint_name: str
    endpoint_target_url: str
    event_id: uuid.UUID
    event_type: str


class DeliveryDetail(BaseModel):
    id: uuid.UUID
    status: str
    total_attempts: int
    next_retry_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime
    endpoint_id: uuid.UUID
    endpoint_name: str
    endpoint_target_url: str
    event_id: uuid.UUID
    event_type: str
    event_payload: dict
    event_created_at: datetime
    attempts: list[DeliveryAttemptRead]
