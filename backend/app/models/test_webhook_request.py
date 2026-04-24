from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.database import Base


class TestWebhookRequest(Base):
    __tablename__ = "test_webhook_requests"
    __test__ = False

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    receiver_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("test_webhook_receivers.id", ondelete="CASCADE"),
        nullable=False,
    )
    method: Mapped[str] = mapped_column(String(16), nullable=False)
    headers: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False)
    body: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSON, nullable=True)
    raw_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    receiver = relationship("TestWebhookReceiver", back_populates="requests")
