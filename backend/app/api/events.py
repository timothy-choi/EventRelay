from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.database import get_db_session
from backend.app.models.delivery import Delivery, DeliveryStatus
from backend.app.models.endpoint import Endpoint
from backend.app.models.event import Event
from backend.app.schemas.event import EventCreate, EventRead
from backend.app.services.queue_service import enqueue_delivery, get_redis_client


router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventRead, status_code=status.HTTP_201_CREATED)
def create_event(payload: EventCreate, session: Session = Depends(get_db_session)) -> Event:
    redis_client = get_redis_client()

    event = Event(
        event_type=payload.event_type,
        payload=payload.payload,
    )
    session.add(event)
    session.flush()

    active_endpoints = list(
        session.execute(
            select(Endpoint).where(Endpoint.is_active.is_(True)).order_by(Endpoint.created_at.asc())
        ).scalars()
    )

    deliveries: list[Delivery] = []
    for endpoint in active_endpoints:
        delivery = Delivery(
            event_id=event.id,
            endpoint_id=endpoint.id,
            status=DeliveryStatus.pending.value,
            total_attempts=0,
        )
        session.add(delivery)
        deliveries.append(delivery)

    session.commit()
    session.refresh(event)

    for delivery in deliveries:
        session.refresh(delivery)
        enqueue_delivery(redis_client, delivery.id)

    return event


@router.get("", response_model=list[EventRead])
def list_events(session: Session = Depends(get_db_session)) -> list[Event]:
    statement = select(Event).order_by(Event.created_at.desc())
    return list(session.execute(statement).scalars().all())
