# EventRelay

EventRelay is the initial MVP backend for a developer-facing webhook delivery platform. The first milestone covers the full async delivery path: register endpoint -> create event -> enqueue delivery -> worker sends webhook -> store delivery results.

## Stack

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Redis
- httpx
- Docker Compose

## Project Structure

```text
backend/
  app/
    main.py
    api/
    models/
    schemas/
    services/
    db/
    worker/
```

## Local Setup

1. Start the full stack:

```bash
docker-compose up --build
```

2. API will be available at:

```text
http://localhost:8000
```

3. Health check:

```bash
curl http://localhost:8000/health
```

## Example Usage

Create an endpoint:

```bash
curl -X POST http://localhost:8000/endpoints \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Local test endpoint",
    "target_url": "https://example.com/webhook"
  }'
```

List endpoints:

```bash
curl http://localhost:8000/endpoints
```

Create an event:

```bash
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "test.event",
    "payload": {
      "message": "hello"
    }
  }'
```

List deliveries:

```bash
curl http://localhost:8000/deliveries
```

Get one delivery with attempts:

```bash
curl http://localhost:8000/deliveries/<delivery_id>
```

## Architecture

- FastAPI exposes endpoint, event, delivery, and health APIs.
- PostgreSQL stores endpoints, events, deliveries, and delivery attempts.
- Redis stores pending delivery IDs in a simple queue.
- A worker process consumes delivery IDs from Redis, sends webhooks with signed headers, and records attempt metadata.
- Retry behavior is intentionally simple for the MVP: retries are handled by the worker with in-process sleep and requeue logic.

## Environment Variables

- `DATABASE_URL`
- `REDIS_URL`

These are configured automatically in `docker-compose.yml` for local development.

## Next Planned Features

- Replay failed deliveries
- Network simulation proxy
- Latency, jitter, and timeout testing
- Dashboard
- AWS deployment
# EventRelay
