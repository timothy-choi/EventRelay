# EventRelay – Network-Aware Webhook Delivery Platform

EventRelay is a distributed event delivery system that simulates real-world network conditions to test webhook reliability.

It is designed to showcase asynchronous fan-out, queue-backed workers, retry behavior, failure classification, proxy-aware networking, and delivery observability in a developer-friendly local stack.

## Key Features

- Async event fan-out from one event to many webhook endpoints
- Retry with exponential backoff for retryable delivery failures
- Delivery failure classification for timeouts, connection errors, DNS errors, and HTTP failures
- Network simulation proxy for latency, injected failures, and timeouts
- Per-endpoint simulation configuration
- Built-in webhook receiver for testing without running an external server
- Delivery observability through attempts, endpoint stats, and system metrics
- Minimal dashboard for endpoints, deliveries, test receivers, and delivery inspection

## Architecture

```text
Client -> API -> DB/Queue -> Worker -> Proxy -> Endpoint
```

Component roles:

- `Client`: creates endpoints, emits events, inspects deliveries, and views metrics
- `API`: accepts events/endpoints and writes durable state to Postgres
- `DB/Queue`: PostgreSQL stores delivery state while Redis holds pending delivery IDs
- `Worker`: consumes queued deliveries asynchronously and manages retries
- `Proxy`: injects latency, timeouts, and failures to simulate unreliable networks
- `Endpoint`: either a real webhook target or EventRelay's built-in test receiver

## Stack

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Redis
- httpx
- Go network simulation proxy
- Next.js dashboard
- Docker Compose

## Local Setup

Start the full stack:

```bash
docker compose up --build
```

Services:

- API: `http://localhost:8000`
- Dashboard: `http://localhost:3000`
- Proxy: `http://localhost:8080`

Health check:

```bash
curl http://localhost:8000/health
```

## Demo

### 1. Create a built-in test receiver

```bash
curl -X POST http://localhost:8000/test-webhooks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "stable-receiver"
  }'
```

This returns a receiver URL like:

```text
http://backend:8000/test-webhooks/<receiver_id>
```

Use that URL as an endpoint target inside Docker.

### 2. Create a stable endpoint

```bash
curl -X POST http://localhost:8000/endpoints \
  -H "Content-Type: application/json" \
  -d '{
    "name": "stable-endpoint",
    "target_url": "http://backend:8000/test-webhooks/<receiver_id>"
  }'
```

### 3. Create an unstable endpoint

```bash
curl -X POST http://localhost:8000/endpoints \
  -H "Content-Type: application/json" \
  -d '{
    "name": "unstable-endpoint",
    "target_url": "http://host.docker.internal:9000/webhook",
    "simulation_latency_ms": 300,
    "simulation_failure_rate": 50,
    "simulation_timeout_rate": 0
  }'
```

### 4. Send an event

```bash
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "demo.network.test",
    "payload": {
      "message": "hello from EventRelay"
    }
  }'
```

### 5. Inspect deliveries

```bash
curl http://localhost:8000/deliveries
```

### 6. Inspect system-wide metrics

```bash
curl http://localhost:8000/system/stats
```

### 7. Inspect built-in receiver traffic

```bash
curl http://localhost:8000/test-webhooks/<receiver_id>/requests
```

## API Highlights

Core workflow:

- `POST /endpoints`
- `GET /endpoints`
- `PATCH /endpoints/{endpoint_id}`
- `POST /events`
- `GET /events`
- `GET /deliveries`
- `GET /deliveries/{delivery_id}`
- `POST /deliveries/{delivery_id}/replay`
- `GET /endpoints/{endpoint_id}/stats`
- `GET /system/stats`

Built-in receiver workflow:

- `POST /test-webhooks`
- `GET /test-webhooks`
- `GET /test-webhooks/{receiver_id}/requests`
- `POST /test-webhooks/{receiver_id}`

## Network Simulation

When proxy mode is enabled, the delivery path becomes:

```text
worker -> proxy -> target webhook endpoint
```

The proxy can inject:

- latency
- synthetic `503` failures
- synthetic timeouts

Per-endpoint simulation fields:

- `simulation_latency_ms`
- `simulation_failure_rate`
- `simulation_timeout_rate`

Example:

```bash
curl -X PATCH http://localhost:8000/endpoints/<endpoint_id> \
  -H "Content-Type: application/json" \
  -d '{
    "simulation_latency_ms": 300,
    "simulation_failure_rate": 50,
    "simulation_timeout_rate": 0
  }'
```

This helps surface how the queue, worker, retries, and observability behave under degraded network conditions.

## Load Testing

Run the load script:

```bash
EVENT_COUNT=100 CONCURRENCY=10 ./scripts/load_test.sh
```

Environment variables:

- `EVENT_COUNT` default: `100`
- `CONCURRENCY` default: `5`
- `API_URL` default: `http://localhost:8000`

The script reports:

- total time taken
- requests per second
- failed request count

What to watch under load:

- event insert throughput at the API
- number of queued deliveries created
- worker retry activity
- delivery status distribution
- latency increase when proxy simulation is enabled

## Observability

### Endpoint stats

```bash
curl http://localhost:8000/endpoints/<endpoint_id>/stats
```

Returns delivery totals, success rate, latency summaries, and failure counts per endpoint.

### System stats

```bash
curl http://localhost:8000/system/stats
```

Returns:

- `total_events_processed`
- `total_deliveries`
- `total_attempts`
- `success_rate`
- `avg_latency_ms`
- `p95_latency_ms`

### Worker logs

Worker logs now include:

- `delivery_id`
- `endpoint_name`
- `attempt_number`
- `latency_ms`
- `failure_type`

This makes it easier to trace delivery outcomes under network stress.

## CI/CD

GitHub Actions validates EventRelay in two layers:

- `pytest` covers unit and integration behavior for the backend and worker services
- a full Docker Compose smoke test boots the entire stack and exercises one real end-to-end flow

The smoke test starts:

- `postgres`
- `redis`
- `backend`
- `worker`
- `proxy`
- `frontend`

It then verifies:

- backend health at `http://localhost:8000/health`
- frontend responds at `http://localhost:3000`
- the API can create a built-in test receiver
- an endpoint can target that built-in receiver through Docker networking
- an event travels through `API -> queue -> worker -> proxy -> built-in receiver`

Run the same check locally:

```bash
./scripts/full_app_smoke_test.sh
```

## Built-in Test Webhook Receiver

EventRelay includes an internal receiver for fast local debugging.

Flow:

1. Create a test receiver
2. Copy the generated internal URL
3. Create an EventRelay endpoint using that URL
4. Send events
5. View the captured request headers and body in the dashboard

This is useful for validating:

- signature headers
- payload shape
- event fan-out behavior
- retry + replay behavior

## Results Template

Use this as a demo/runbook template after load or resilience tests:

- Total events: `<count>`
- Total deliveries: `<count>`
- Success rate: `<percent>`
- Average latency: `<ms>`
- P95 latency: `<ms>`
- Retryable failures observed: `<count>`
- Final failed deliveries: `<count>`

## Migrations

Run migrations locally:

```bash
export DATABASE_URL=postgresql+psycopg://hookhub:hookhub@localhost:5432/hookhub
alembic upgrade head
```

Create a new migration:

```bash
alembic revision --autogenerate -m "describe the change"
```

## Testing

Run tests:

```bash
pytest -q
```

CI runs:

- Alembic migrations
- backend pytest suite

The load test script is intentionally not run in CI.
