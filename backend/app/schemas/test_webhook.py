from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class TestWebhookReceiverCreate(BaseModel):
    __test__ = False
    name: str


class TestWebhookReceiverRead(BaseModel):
    __test__ = False
    id: uuid.UUID
    name: str
    url: str
    created_at: datetime


class TestWebhookRequestRead(BaseModel):
    __test__ = False
    id: uuid.UUID
    receiver_id: uuid.UUID
    method: str
    headers: dict[str, str]
    body: dict[str, Any] | list[Any] | None
    raw_body: str | None
    received_at: datetime
