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
- Go network simulation proxy

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
proxy/
  main.go
  Dockerfile
  README.md
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

Create an endpoint with simulation settings:

```bash
curl -X POST http://localhost:8000/endpoints \
  -H "Content-Type: application/json" \
  -d '{
    "name": "failure-test",
    "target_url": "http://host.docker.internal:9000/webhook",
    "simulation_latency_ms": 100,
    "simulation_failure_rate": 50,
    "simulation_timeout_rate": 0
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
- A Go proxy can sit between the worker and the final webhook target to inject latency, timeouts, and synthetic failures for reliability testing.
- Retry behavior is intentionally simple for the MVP: retries are handled by the worker with in-process sleep and requeue logic.

## Environment Variables

- `DATABASE_URL`
- `REDIS_URL`
- `USE_NETWORK_PROXY`
- `NETWORK_PROXY_URL`

These are configured automatically in `docker-compose.yml` for local development.

## Network Simulation Proxy

The worker can optionally deliver through a dedicated proxy instead of posting directly to the endpoint:

```text
worker -> proxy -> target webhook endpoint
```

When proxy mode is enabled, the worker sends the original webhook payload and signature headers to `NETWORK_PROXY_URL` and includes:

- `X-EventRelay-Target-Url`
- `X-EventRelay-Latency-Ms`
- `X-EventRelay-Timeout-Rate`
- `X-EventRelay-Failure-Rate`

This helps test how delivery retries, failure handling, and observability behave under slower or less reliable network conditions.

Example latency simulation:

```bash
docker-compose up --build
```

With the default compose config, the worker uses the proxy and applies a `300ms` delay before forwarding each webhook. You can adjust the worker environment variables in `docker-compose.yml` to simulate different conditions.

Proxy logs include:

- target URL
- latency applied
- whether a failure was injected
- forwarded response status

## Network Simulation Per Endpoint

Each endpoint can define its own network simulation settings, which the worker forwards to the proxy when `USE_NETWORK_PROXY=true`.

Example:

```bash
curl -X POST http://localhost:8000/endpoints \
  -H "Content-Type: application/json" \
  -d '{
    "name": "failure-test",
    "target_url": "http://host.docker.internal:9000/webhook",
    "simulation_latency_ms": 100,
    "simulation_failure_rate": 50,
    "simulation_timeout_rate": 0
  }'
```

- `simulation_latency_ms` adds delay before forwarding the webhook.
- `simulation_failure_rate` injects synthetic `503` responses without forwarding.
- `simulation_timeout_rate` simulates delivery timeouts by delaying long enough for the worker request to time out.

Endpoints without simulation values continue to behave the same way, using `0` for all simulation settings.

## Next Planned Features

- Replay failed deliveries
- Latency, jitter, and timeout testing
- Dashboard
- AWS deployment
