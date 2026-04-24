from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.delivery import Delivery
from backend.app.models.delivery_attempt import DeliveryAttempt
from backend.app.models.event import Event
from backend.app.schemas.system import SystemStatsRead
from backend.app.services.queue_service import get_metric_counter, get_queue_depth


def calculate_latency_metrics(latencies: list[int]) -> tuple[float | None, float | None]:
    if not latencies:
        return None, None

    sorted_latencies = sorted(latencies)
    avg_latency_ms = sum(sorted_latencies) / len(sorted_latencies)
    p95_index = max(0, -(-95 * len(sorted_latencies) // 100) - 1)
    p95_latency_ms = float(sorted_latencies[p95_index])
    return avg_latency_ms, p95_latency_ms


def get_system_stats(session: Session, redis_client) -> SystemStatsRead:
    total_events_processed = session.scalar(select(func.count()).select_from(Event)) or 0
    total_deliveries = session.scalar(select(func.count()).select_from(Delivery)) or 0
    total_attempts = session.scalar(select(func.count()).select_from(DeliveryAttempt)) or 0
    succeeded_deliveries = (
        session.scalar(
            select(func.count()).select_from(Delivery).where(Delivery.status == "succeeded")
        )
        or 0
    )

    latencies = list(
        session.execute(
            select(DeliveryAttempt.latency_ms).where(DeliveryAttempt.latency_ms.is_not(None))
        ).scalars()
    )
    avg_latency_ms, p95_latency_ms = calculate_latency_metrics(latencies)

    success_rate = (succeeded_deliveries / total_deliveries * 100) if total_deliveries else 0.0
    rate_limited_count = get_metric_counter(redis_client, "rate_limited_count")
    delayed_due_to_backpressure_count = get_metric_counter(
        redis_client,
        "delayed_due_to_backpressure_count",
    )
    current_queue_depth = get_queue_depth(redis_client)

    return SystemStatsRead(
        total_events_processed=total_events_processed,
        total_deliveries=total_deliveries,
        total_attempts=total_attempts,
        success_rate=success_rate,
        avg_latency_ms=avg_latency_ms,
        p95_latency_ms=p95_latency_ms,
        rate_limited_count=rate_limited_count,
        delayed_due_to_backpressure_count=delayed_due_to_backpressure_count,
        current_queue_depth=current_queue_depth,
    )
