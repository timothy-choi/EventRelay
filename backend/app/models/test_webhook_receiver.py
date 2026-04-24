from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.database import Base


class TestWebhookReceiver(Base):
    __tablename__ = "test_webhook_receivers"
    __test__ = False

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    requests = relationship(
        "TestWebhookRequest",
        back_populates="receiver",
        cascade="all, delete-orphan",
        order_by="TestWebhookRequest.received_at.desc()",
    )
