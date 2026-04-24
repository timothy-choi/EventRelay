from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.database import get_db_session
from backend.app.models.test_webhook_receiver import TestWebhookReceiver
from backend.app.models.test_webhook_request import TestWebhookRequest
from backend.app.schemas.test_webhook import (
    TestWebhookReceiverCreate,
    TestWebhookReceiverRead,
    TestWebhookRequestRead,
)


router = APIRouter(prefix="/test-webhooks", tags=["test-webhooks"])

MAX_HEADER_VALUE_LENGTH = 2048
MAX_RAW_BODY_LENGTH = 10000
PUBLIC_API_URL = os.getenv("PUBLIC_API_URL", "http://localhost:8000")


def build_receiver_url(receiver_id: UUID) -> str:
    return f"{PUBLIC_API_URL.rstrip('/')}/test-webhooks/{receiver_id}"


def serialize_receiver(receiver: TestWebhookReceiver) -> TestWebhookReceiverRead:
    return TestWebhookReceiverRead(
        id=receiver.id,
        name=receiver.name,
        url=build_receiver_url(receiver.id),
        created_at=receiver.created_at,
    )


def sanitize_headers(request: Request) -> dict[str, str]:
    filtered: dict[str, str] = {}
    allowed_prefixes = ("content-", "x-", "user-agent", "accept", "host")

    for key, value in request.headers.items():
        key_lower = key.lower()
        if key_lower.startswith(allowed_prefixes) or key_lower in {"authorization"}:
            filtered[key] = value[:MAX_HEADER_VALUE_LENGTH]

    return filtered


def parse_request_body(raw_body: bytes) -> tuple[dict | list | None, str | None]:
    if not raw_body:
        return None, None

    decoded_body = raw_body.decode("utf-8", errors="replace")
    truncated_body = decoded_body[:MAX_RAW_BODY_LENGTH]

    try:
        parsed_body = json.loads(decoded_body)
    except json.JSONDecodeError:
        parsed_body = None

    return parsed_body, truncated_body


@router.post("", response_model=TestWebhookReceiverRead, status_code=status.HTTP_201_CREATED)
def create_test_webhook_receiver(
    payload: TestWebhookReceiverCreate,
    session: Session = Depends(get_db_session),
) -> TestWebhookReceiverRead:
    receiver = TestWebhookReceiver(name=payload.name)
    session.add(receiver)
    session.commit()
    session.refresh(receiver)
    return serialize_receiver(receiver)


@router.get("", response_model=list[TestWebhookReceiverRead])
def list_test_webhook_receivers(session: Session = Depends(get_db_session)) -> list[TestWebhookReceiverRead]:
    receivers = list(
        session.execute(
            select(TestWebhookReceiver).order_by(TestWebhookReceiver.created_at.desc())
        ).scalars()
    )
    return [serialize_receiver(receiver) for receiver in receivers]


@router.get("/{receiver_id}/requests", response_model=list[TestWebhookRequestRead])
def list_test_webhook_requests(
    receiver_id: UUID,
    session: Session = Depends(get_db_session),
) -> list[TestWebhookRequestRead]:
    receiver = session.get(TestWebhookReceiver, receiver_id)
    if receiver is None:
        raise HTTPException(status_code=404, detail="Test webhook receiver not found")

    requests = list(
        session.execute(
            select(TestWebhookRequest)
            .where(TestWebhookRequest.receiver_id == receiver_id)
            .order_by(TestWebhookRequest.received_at.desc())
        ).scalars()
    )
    return [
        TestWebhookRequestRead(
            id=request.id,
            receiver_id=request.receiver_id,
            method=request.method,
            headers=request.headers,
            body=request.body,
            raw_body=request.raw_body,
            received_at=request.received_at,
        )
        for request in requests
    ]


@router.post("/{receiver_id}")
async def receive_test_webhook(
    receiver_id: UUID,
    request: Request,
    session: Session = Depends(get_db_session),
) -> dict[str, str]:
    receiver = session.get(TestWebhookReceiver, receiver_id)
    if receiver is None:
        raise HTTPException(status_code=404, detail="Test webhook receiver not found")

    raw_body = await request.body()
    parsed_body, truncated_body = parse_request_body(raw_body)

    stored_request = TestWebhookRequest(
        receiver_id=receiver.id,
        method=request.method,
        headers=sanitize_headers(request),
        body=parsed_body,
        raw_body=truncated_body,
        received_at=datetime.now(timezone.utc),
    )
    session.add(stored_request)
    session.commit()

    return {"status": "received"}
