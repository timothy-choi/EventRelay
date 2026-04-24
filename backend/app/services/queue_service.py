from __future__ import annotations

import os
import uuid

from redis import Redis


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DELIVERY_QUEUE_NAME = "deliveries:queue"


def get_redis_client() -> Redis:
    return Redis.from_url(REDIS_URL, decode_responses=True)


def enqueue_delivery(redis_client: Redis, delivery_id: uuid.UUID) -> None:
    redis_client.lpush(DELIVERY_QUEUE_NAME, str(delivery_id))


def dequeue_delivery(redis_client: Redis, timeout: int = 5) -> str | None:
    result = redis_client.brpop(DELIVERY_QUEUE_NAME, timeout=timeout)
    if result is None:
        return None
    _, delivery_id = result
    return delivery_id
