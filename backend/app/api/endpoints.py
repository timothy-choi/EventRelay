from __future__ import annotations

import secrets
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.database import get_db_session
from backend.app.models.endpoint import Endpoint
from backend.app.schemas.endpoint import EndpointCreate, EndpointRead, EndpointUpdate


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
