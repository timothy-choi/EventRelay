#!/usr/bin/env bash
set -euo pipefail

EVENT_COUNT="${EVENT_COUNT:-100}"
CONCURRENCY="${CONCURRENCY:-5}"
API_URL="${API_URL:-http://localhost:8000}"

python3 - "$EVENT_COUNT" "$CONCURRENCY" "$API_URL" <<'PY'
import asyncio
import json
import sys
import time
from urllib import request


event_count = int(sys.argv[1])
concurrency = int(sys.argv[2])
api_url = sys.argv[3].rstrip("/")


def post_event(index: int) -> int:
    payload = json.dumps(
        {
            "event_type": "load.test",
            "payload": {
                "sequence": index,
                "message": "load test event",
            },
        }
    ).encode("utf-8")
    req = request.Request(
        f"{api_url}/events",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=30) as response:
        return response.status


async def main() -> None:
    semaphore = asyncio.Semaphore(concurrency)
    loop = asyncio.get_running_loop()
    failures = 0

    async def run_one(index: int) -> None:
        nonlocal failures
        async with semaphore:
            try:
                status = await loop.run_in_executor(None, post_event, index)
                if status not in {200, 201}:
                    failures += 1
            except Exception:
                failures += 1

    start = time.perf_counter()
    await asyncio.gather(*(run_one(i) for i in range(1, event_count + 1)))
    duration = time.perf_counter() - start
    rps = event_count / duration if duration > 0 else 0.0

    print(f"Sent {event_count} events")
    print(f"Concurrency: {concurrency}")
    print(f"Total time: {duration:.2f}s")
    print(f"Requests/sec: {rps:.2f}")
    print(f"Failures: {failures}")


asyncio.run(main())
PY
