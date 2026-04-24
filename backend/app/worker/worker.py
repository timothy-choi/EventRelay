from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from backend.app.db.database import SessionLocal, init_db
from backend.app.services.delivery_service import process_delivery
from backend.app.services.queue_service import dequeue_delivery, get_redis_client


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def run_worker() -> None:
    init_db()
    redis_client = get_redis_client()
    logger.info("Worker started and listening for deliveries")

    while True:
        delivery_id_raw = dequeue_delivery(redis_client, timeout=5)
        if delivery_id_raw is None:
            await asyncio.sleep(1)
            continue

        try:
            delivery_id = UUID(delivery_id_raw)
        except ValueError:
            logger.warning("Skipping invalid delivery ID from queue: %s", delivery_id_raw)
            continue

        session = SessionLocal()
        try:
            await process_delivery(session, redis_client, delivery_id)
        except Exception:
            logger.exception("Unexpected worker error while processing delivery %s", delivery_id)
            session.rollback()
        finally:
            session.close()


def main() -> None:
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
