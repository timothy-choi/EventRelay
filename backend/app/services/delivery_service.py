from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload

from backend.app.models.delivery import Delivery, DeliveryStatus
from backend.app.models.delivery_attempt import DeliveryAttempt
from backend.app.services.queue_service import enqueue_delivery
from backend.app.services.webhook_sender import WebhookSendResult, send_webhook


RETRY_DELAYS_SECONDS = {
    1: 30,
    2: 120,
}
MAX_ATTEMPTS = 3


def list_delivery_rows() -> Select[tuple[Delivery]]:
    return select(Delivery).options(
        joinedload(Delivery.endpoint),
        joinedload(Delivery.event),
    )


def get_delivery_by_id(session: Session, delivery_id: UUID) -> Delivery | None:
    statement = (
        select(Delivery)
        .where(Delivery.id == delivery_id)
        .options(
            joinedload(Delivery.endpoint),
            joinedload(Delivery.event),
            joinedload(Delivery.attempts),
        )
    )
    return session.execute(statement).unique().scalar_one_or_none()


def create_attempt_record(
    session: Session,
    delivery: Delivery,
    attempt_number: int,
    result: WebhookSendResult,
    started_at: datetime,
) -> DeliveryAttempt:
    attempt = DeliveryAttempt(
        delivery_id=delivery.id,
        attempt_number=attempt_number,
        status=result.status,
        response_code=result.response_code,
        latency_ms=result.latency_ms,
        failure_type=result.failure_type,
        error_message=result.error_message,
        started_at=started_at,
        completed_at=datetime.now(timezone.utc),
    )
    session.add(attempt)
    return attempt


async def process_delivery(session: Session, redis_client, delivery_id: UUID) -> None:
    delivery = get_delivery_by_id(session, delivery_id)
    if delivery is None:
        return

    if not delivery.endpoint.is_active:
        delivery.status = DeliveryStatus.failed.value
        delivery.last_error = "Endpoint is inactive"
        delivery.updated_at = datetime.now(timezone.utc)
        session.commit()
        return

    attempt_number = delivery.total_attempts + 1
    delivery.status = DeliveryStatus.delivering.value
    delivery.updated_at = datetime.now(timezone.utc)
    session.commit()

    started_at = datetime.now(timezone.utc)
    result = await send_webhook(delivery.endpoint, delivery.event)

    create_attempt_record(
        session=session,
        delivery=delivery,
        attempt_number=attempt_number,
        result=result,
        started_at=started_at,
    )

    delivery.total_attempts = attempt_number
    delivery.last_error = result.error_message
    delivery.updated_at = datetime.now(timezone.utc)

    if result.status == DeliveryStatus.succeeded.value:
        delivery.status = DeliveryStatus.succeeded.value
        delivery.next_retry_at = None
        session.commit()
        return

    if attempt_number >= MAX_ATTEMPTS or result.status == DeliveryStatus.failed.value:
        delivery.status = DeliveryStatus.failed.value
        delivery.next_retry_at = None
        session.commit()
        return

    retry_delay = RETRY_DELAYS_SECONDS.get(attempt_number)
    if retry_delay is None:
        delivery.status = DeliveryStatus.failed.value
        delivery.next_retry_at = None
        session.commit()
        return

    delivery.status = DeliveryStatus.retrying.value
    delivery.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=retry_delay)
    session.commit()

    await asyncio.sleep(retry_delay)
    enqueue_delivery(redis_client, delivery.id)
