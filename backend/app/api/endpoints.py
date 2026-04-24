from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.database import get_db_session
from backend.app.models.endpoint import Endpoint
from backend.app.schemas.endpoint import EndpointCreate, EndpointRead


router = APIRouter(prefix="/endpoints", tags=["endpoints"])


@router.post("", response_model=EndpointRead, status_code=status.HTTP_201_CREATED)
def create_endpoint(payload: EndpointCreate, session: Session = Depends(get_db_session)) -> Endpoint:
    endpoint = Endpoint(
        name=payload.name,
        target_url=str(payload.target_url),
        signing_secret=secrets.token_hex(32),
        is_active=True,
    )
    session.add(endpoint)
    session.commit()
    session.refresh(endpoint)
    return endpoint


@router.get("", response_model=list[EndpointRead])
def list_endpoints(session: Session = Depends(get_db_session)) -> list[Endpoint]:
    statement = select(Endpoint).order_by(Endpoint.created_at.desc())
    return list(session.execute(statement).scalars().all())
