from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, HttpUrl


class EndpointCreate(BaseModel):
    name: str
    target_url: HttpUrl


class EndpointRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    target_url: str
    is_active: bool
    created_at: datetime


class EndpointUpdate(BaseModel):
    is_active: Optional[bool] = None
