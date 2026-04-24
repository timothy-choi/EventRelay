from __future__ import annotations

import os
import time
import uuid

from redis import Redis


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DELIVERY_QUEUE_NAME = "deliveries:queue"
RATE_LIMIT_PREFIX = "rate_limit"
METRICS_PREFIX = "metrics"


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


def get_queue_depth(redis_client: Redis) -> int:
    return int(redis_client.llen(DELIVERY_QUEUE_NAME))


def increment_metric_counter(redis_client: Redis, metric_name: str) -> int:
    return int(redis_client.incr(f"{METRICS_PREFIX}:{metric_name}"))


def get_metric_counter(redis_client: Redis, metric_name: str) -> int:
    value = redis_client.get(f"{METRICS_PREFIX}:{metric_name}")
    return int(value) if value is not None else 0


def consume_rate_limit_slot(redis_client: Redis, endpoint_id: uuid.UUID) -> int:
    current_second = int(time.time())
    key = f"{RATE_LIMIT_PREFIX}:{endpoint_id}:{current_second}"
    count = int(redis_client.incr(key))
    if count == 1:
        redis_client.expire(key, 1)
    return count
