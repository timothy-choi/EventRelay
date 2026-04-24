from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload

from backend.app.models.delivery import Delivery, DeliveryStatus
from backend.app.models.delivery_attempt import DeliveryAttempt
from backend.app.services.queue_service import (
    consume_rate_limit_slot,
    enqueue_delivery,
    get_queue_depth,
    increment_metric_counter,
)
from backend.app.services.webhook_sender import (
    WebhookSendResult,
    is_retryable_failure,
    send_webhook,
)


RETRY_DELAYS_SECONDS = {
    1: 30,
    2: 120,
}
MAX_ATTEMPTS = 3
BACKPRESSURE_QUEUE_THRESHOLD = 100
BACKPRESSURE_DELAY_SECONDS = 0.05
RATE_LIMIT_RETRY_SECONDS = 1
logger = logging.getLogger(__name__)


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


def create_delivery(
    session: Session,
    *,
    event_id: UUID,
    endpoint_id: UUID,
) -> Delivery:
    delivery = Delivery(
        event_id=event_id,
        endpoint_id=endpoint_id,
        status=DeliveryStatus.pending.value,
        total_attempts=0,
        next_retry_at=None,
        last_error=None,
    )
    session.add(delivery)
    session.flush()
    return delivery


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


def schedule_retry(
    session: Session,
    redis_client,
    delivery: Delivery,
    retry_delay: int,
) -> None:
    delivery_id = delivery.id
    delivery.status = DeliveryStatus.retrying.value
    delivery.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=retry_delay)
    delivery.updated_at = datetime.now(timezone.utc)
    session.commit()

    async def _requeue() -> None:
        await asyncio.sleep(retry_delay)
        enqueue_delivery(redis_client, delivery_id)

    asyncio.create_task(_requeue())


def schedule_deferred_delivery(
    session: Session,
    redis_client,
    delivery: Delivery,
    delay_seconds: int,
    *,
    status: str,
    last_error: str | None = None,
) -> None:
    delivery_id = delivery.id
    delivery.status = status
    delivery.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
    delivery.last_error = last_error
    delivery.updated_at = datetime.now(timezone.utc)
    session.commit()

    async def _requeue() -> None:
        await asyncio.sleep(delay_seconds)
        enqueue_delivery(redis_client, delivery_id)

    asyncio.create_task(_requeue())


async def process_delivery(session: Session, redis_client, delivery_id: UUID) -> None:
    delivery = get_delivery_by_id(session, delivery_id)
    if delivery is None:
        return

    if not delivery.endpoint.is_active:
        delivery.status = DeliveryStatus.failed.value
        delivery.last_error = "Endpoint is inactive"
        delivery.next_retry_at = None
        delivery.updated_at = datetime.now(timezone.utc)
        session.commit()
        logger.info(
            "delivery_id=%s endpoint_name=%s attempt_number=%s latency_ms=%s failure_type=%s status=%s",
            delivery.id,
            delivery.endpoint.name,
            0,
            None,
            "endpoint_inactive",
            delivery.status,
        )
        return

    queue_depth = get_queue_depth(redis_client)
    if queue_depth > BACKPRESSURE_QUEUE_THRESHOLD:
        increment_metric_counter(redis_client, "delayed_due_to_backpressure_count")
        await asyncio.sleep(BACKPRESSURE_DELAY_SECONDS)

    max_requests_per_second = getattr(delivery.endpoint, "max_requests_per_second", 0) or 0
    if max_requests_per_second > 0:
        slot_count = consume_rate_limit_slot(redis_client, delivery.endpoint.id)
        if slot_count > max_requests_per_second:
            increment_metric_counter(redis_client, "rate_limited_count")
            schedule_deferred_delivery(
                session,
                redis_client,
                delivery,
                RATE_LIMIT_RETRY_SECONDS,
                status=DeliveryStatus.pending.value,
                last_error="rate_limited",
            )
            logger.info(
                "rate_limited endpoint=%s scheduled_retry_at=%s",
                delivery.endpoint.id,
                delivery.next_retry_at,
            )
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

    logger.info(
        "delivery_id=%s endpoint_name=%s attempt_number=%s latency_ms=%s failure_type=%s status=%s",
        delivery.id,
        delivery.endpoint.name,
        attempt_number,
        result.latency_ms,
        result.failure_type,
        result.status,
    )

    if result.status == DeliveryStatus.succeeded.value:
        delivery.status = DeliveryStatus.succeeded.value
        delivery.next_retry_at = None
        session.commit()
        return

    retryable = is_retryable_failure(result.failure_type)
    if attempt_number >= MAX_ATTEMPTS or not retryable:
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

    schedule_retry(session, redis_client, delivery, retry_delay)
