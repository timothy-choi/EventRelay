from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db.database import get_db_session
from backend.app.schemas.delivery import DeliveryAttemptRead, DeliveryDetail, DeliveryListItem
from backend.app.services.delivery_service import get_delivery_by_id, list_delivery_rows


router = APIRouter(prefix="/deliveries", tags=["deliveries"])


@router.get("", response_model=list[DeliveryListItem])
def list_deliveries(session: Session = Depends(get_db_session)) -> list[DeliveryListItem]:
    deliveries = session.execute(list_delivery_rows()).unique().scalars().all()
    return [
        DeliveryListItem(
            id=delivery.id,
            status=delivery.status,
            total_attempts=delivery.total_attempts,
            next_retry_at=delivery.next_retry_at,
            last_error=delivery.last_error,
            created_at=delivery.created_at,
            updated_at=delivery.updated_at,
            endpoint_id=delivery.endpoint.id,
            endpoint_name=delivery.endpoint.name,
            endpoint_target_url=delivery.endpoint.target_url,
            event_id=delivery.event.id,
            event_type=delivery.event.event_type,
        )
        for delivery in deliveries
    ]


@router.get("/{delivery_id}", response_model=DeliveryDetail)
def get_delivery(delivery_id: UUID, session: Session = Depends(get_db_session)) -> DeliveryDetail:
    delivery = get_delivery_by_id(session, delivery_id)
    if delivery is None:
        raise HTTPException(status_code=404, detail="Delivery not found")

    return DeliveryDetail(
        id=delivery.id,
        status=delivery.status,
        total_attempts=delivery.total_attempts,
        next_retry_at=delivery.next_retry_at,
        last_error=delivery.last_error,
        created_at=delivery.created_at,
        updated_at=delivery.updated_at,
        endpoint_id=delivery.endpoint.id,
        endpoint_name=delivery.endpoint.name,
        endpoint_target_url=delivery.endpoint.target_url,
        event_id=delivery.event.id,
        event_type=delivery.event.event_type,
        event_payload=delivery.event.payload,
        event_created_at=delivery.event.created_at,
        attempts=[
            DeliveryAttemptRead(
                id=attempt.id,
                attempt_number=attempt.attempt_number,
                status=attempt.status,
                response_code=attempt.response_code,
                latency_ms=attempt.latency_ms,
                failure_type=attempt.failure_type,
                error_message=attempt.error_message,
                started_at=attempt.started_at,
                completed_at=attempt.completed_at,
            )
            for attempt in delivery.attempts
        ],
    )
