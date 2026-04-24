from __future__ import annotations

import secrets
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.database import get_db_session
from backend.app.models.delivery import Delivery
from backend.app.models.delivery_attempt import DeliveryAttempt
from backend.app.models.endpoint import Endpoint
from backend.app.schemas.endpoint import EndpointCreate, EndpointRead, EndpointStatsRead, EndpointUpdate
from backend.app.services.stats_service import calculate_latency_metrics


router = APIRouter(prefix="/endpoints", tags=["endpoints"])


@router.post("", response_model=EndpointRead, status_code=status.HTTP_201_CREATED)
def create_endpoint(payload: EndpointCreate, session: Session = Depends(get_db_session)) -> Endpoint:
    endpoint = Endpoint(
        name=payload.name,
        target_url=str(payload.target_url),
        signing_secret=secrets.token_hex(32),
        is_active=True,
        simulation_latency_ms=payload.simulation_latency_ms,
        simulation_failure_rate=payload.simulation_failure_rate,
        simulation_timeout_rate=payload.simulation_timeout_rate,
    )
    session.add(endpoint)
    session.commit()
    session.refresh(endpoint)
    return endpoint


@router.get("", response_model=list[EndpointRead])
def list_endpoints(session: Session = Depends(get_db_session)) -> list[Endpoint]:
    statement = select(Endpoint).order_by(Endpoint.created_at.desc())
    return list(session.execute(statement).scalars().all())


@router.patch("/{endpoint_id}", response_model=EndpointRead)
def update_endpoint(
    endpoint_id: UUID,
    payload: EndpointUpdate,
    session: Session = Depends(get_db_session),
) -> Endpoint:
    endpoint = session.get(Endpoint, endpoint_id)
    if endpoint is None:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    update_data = payload.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(endpoint, key, value)

    session.add(endpoint)
    session.commit()
    session.refresh(endpoint)
    return endpoint


@router.get("/{endpoint_id}/stats", response_model=EndpointStatsRead)
def get_endpoint_stats(
    endpoint_id: UUID,
    session: Session = Depends(get_db_session),
) -> EndpointStatsRead:
    endpoint = session.get(Endpoint, endpoint_id)
    if endpoint is None:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    deliveries = list(
        session.execute(
            select(Delivery).where(Delivery.endpoint_id == endpoint_id).order_by(Delivery.created_at.asc())
        ).scalars()
    )
    attempts = list(
        session.execute(
            select(DeliveryAttempt)
            .join(Delivery, DeliveryAttempt.delivery_id == Delivery.id)
            .where(Delivery.endpoint_id == endpoint_id)
            .order_by(DeliveryAttempt.started_at.asc())
        ).scalars()
    )

    total_deliveries = len(deliveries)
    status_counts = {
        "succeeded": 0,
        "failed": 0,
        "retrying": 0,
        "pending": 0,
    }
    for delivery in deliveries:
        if delivery.status in status_counts:
            status_counts[delivery.status] += 1

    latencies = [attempt.latency_ms for attempt in attempts if attempt.latency_ms is not None]
    avg_latency_ms, p95_latency_ms = calculate_latency_metrics(latencies)

    failure_counts = {
        "timeout": 0,
        "connection_error": 0,
        "http_4xx": 0,
        "http_5xx": 0,
    }
    for attempt in attempts:
        if attempt.failure_type in failure_counts:
            failure_counts[attempt.failure_type] += 1

    success_rate = (status_counts["succeeded"] / total_deliveries * 100) if total_deliveries else 0.0

    return EndpointStatsRead(
        endpoint_id=endpoint.id,
        endpoint_name=endpoint.name,
        total_deliveries=total_deliveries,
        succeeded=status_counts["succeeded"],
        failed=status_counts["failed"],
        retrying=status_counts["retrying"],
        pending=status_counts["pending"],
        success_rate=success_rate,
        avg_latency_ms=avg_latency_ms,
        p95_latency_ms=p95_latency_ms,
        total_attempts=len(attempts),
        timeout_count=failure_counts["timeout"],
        connection_error_count=failure_counts["connection_error"],
        http_4xx_count=failure_counts["http_4xx"],
        http_5xx_count=failure_counts["http_5xx"],
    )
