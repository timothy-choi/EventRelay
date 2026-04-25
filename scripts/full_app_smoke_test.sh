#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

API_BASE_URL="${API_BASE_URL:-${API_URL:-http://localhost:8000}}"
FRONTEND_BASE_URL="${FRONTEND_BASE_URL:-${FRONTEND_URL:-http://localhost:3000}}"
SMOKE_EVENT_TYPE="${SMOKE_EVENT_TYPE:-ci.full_app.smoke}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-120}"
POLL_INTERVAL_SECONDS="${POLL_INTERVAL_SECONDS:-2}"
START_COMPOSE="${START_COMPOSE:-auto}"
RECEIVER_TARGET_BASE_URL="${RECEIVER_TARGET_BASE_URL:-}"

receiver_id=""
endpoint_id=""
delivery_id=""

print_section() {
  printf '\n==> %s\n' "$1"
}

dump_logs() {
  if [[ "${compose_started:-false}" != "true" ]]; then
    return 0
  fi

  print_section "docker compose ps"
  docker compose ps || true

  for service in backend worker proxy frontend postgres redis; do
    print_section "${service} logs"
    docker compose logs "$service" --tail=200 || true
  done
}

cleanup() {
  if [[ "$compose_started" == "true" ]]; then
    print_section "Cleaning up Docker Compose resources"
    docker compose down -v || true
  fi
}

finalize() {
  local status=$?
  if [[ "$status" -ne 0 ]]; then
    print_section "Smoke test failed"
    dump_logs
  fi
  cleanup
  exit "$status"
}

trap finalize EXIT

wait_for_http() {
  local name="$1"
  local url="$2"
  local deadline=$((SECONDS + TIMEOUT_SECONDS))

  while (( SECONDS < deadline )); do
    if curl -fsS "$url" >/dev/null; then
      echo "$name is ready at $url"
      return 0
    fi
    sleep "$POLL_INTERVAL_SECONDS"
  done

  echo "Timed out waiting for $name at $url" >&2
  return 1
}

should_start_compose() {
  if [[ "$START_COMPOSE" == "true" ]]; then
    return 0
  fi

  if [[ "$START_COMPOSE" == "false" ]]; then
    return 1
  fi

  [[ "$API_BASE_URL" == "http://localhost:8000" && "$FRONTEND_BASE_URL" == "http://localhost:3000" ]]
}

python_json_field() {
  local field="$1"
  python3 -c 'import json, sys; data = json.load(sys.stdin); value = data'"$field"'; print("" if value is None else value)'
}

compose_started="false"
if should_start_compose; then
  print_section "Building and starting full app stack"
  docker compose up -d --build
  compose_started="true"
else
  print_section "Using existing deployed app"
  echo "API_BASE_URL=$API_BASE_URL"
  echo "FRONTEND_BASE_URL=$FRONTEND_BASE_URL"
fi

print_section "Waiting for backend and frontend"
wait_for_http "backend health" "$API_BASE_URL/health"
wait_for_http "frontend" "$FRONTEND_BASE_URL"

print_section "Verifying frontend returns HTTP 200"
frontend_status="$(curl -s -o /dev/null -w '%{http_code}' "$FRONTEND_BASE_URL")"
if [[ "$frontend_status" != "200" ]]; then
  echo "Frontend returned unexpected status: $frontend_status" >&2
  exit 1
fi

if [[ "$compose_started" == "true" ]]; then
  print_section "Verifying containers are running"
  docker compose ps

  for service in postgres redis proxy backend worker frontend; do
    if ! docker compose ps --services --status running | grep -qx "$service"; then
      echo "Expected service '$service' to be running" >&2
      exit 1
    fi
  done
fi

print_section "Creating built-in test webhook receiver"
receiver_response="$(curl -fsS -X POST "$API_BASE_URL/test-webhooks" \
  -H "Content-Type: application/json" \
  -d '{"name":"ci-smoke-receiver"}')"
echo "$receiver_response"
receiver_id="$(printf '%s' "$receiver_response" | python_json_field '["id"]')"
receiver_url="$(printf '%s' "$receiver_response" | python_json_field '["url"]')"
if [[ -n "$RECEIVER_TARGET_BASE_URL" ]]; then
  receiver_url="${RECEIVER_TARGET_BASE_URL%/}/test-webhooks/${receiver_id}"
fi

print_section "Creating endpoint pointing to built-in receiver"
endpoint_response="$(curl -fsS -X POST "$API_BASE_URL/endpoints" \
  -H "Content-Type: application/json" \
  -d "$(python3 - "$receiver_url" <<'PY'
import json
import sys

receiver_url = sys.argv[1]
print(json.dumps({
    "name": "ci-smoke-endpoint",
    "target_url": receiver_url,
}))
PY
)")"
echo "$endpoint_response"
endpoint_id="$(printf '%s' "$endpoint_response" | python_json_field '["id"]')"

print_section "Sending smoke event"
event_response="$(curl -fsS -X POST "$API_BASE_URL/events" \
  -H "Content-Type: application/json" \
  -d "$(python3 - "$SMOKE_EVENT_TYPE" <<'PY'
import json
import sys

event_type = sys.argv[1]
print(json.dumps({
    "event_type": event_type,
    "payload": {
        "source": "github-actions",
        "kind": "full-app-smoke",
    },
}))
PY
)")"
echo "$event_response"
event_id="$(printf '%s' "$event_response" | python_json_field '["id"]')"

print_section "Polling deliveries until one succeeds"
delivery_deadline=$((SECONDS + TIMEOUT_SECONDS))
while (( SECONDS < delivery_deadline )); do
  delivery_result="$(python3 - "$API_BASE_URL" "$endpoint_id" "$event_id" <<'PY'
import json
import sys
import urllib.request

api_url = sys.argv[1]
endpoint_id = sys.argv[2]
event_id = sys.argv[3]

with urllib.request.urlopen(f"{api_url}/deliveries", timeout=10) as response:
    raw = response.read().decode()

deliveries = json.loads(raw)

match = None
for delivery in deliveries:
    if delivery.get("endpoint_id") == endpoint_id and delivery.get("event_id") == event_id:
        match = delivery
        break

if not match:
    print("missing")
else:
    print(f'{match["status"]}|{match["id"]}|{match.get("next_retry_at") or ""}|{match.get("last_error") or ""}')
PY
)"

  IFS='|' read -r delivery_status delivery_id next_retry_at last_error <<<"$delivery_result"

  if [[ "$delivery_status" == "succeeded" ]]; then
    echo "Delivery succeeded: $delivery_id"
    break
  fi

  echo "Current delivery status: ${delivery_status} delivery_id=${delivery_id:-n/a} next_retry_at=${next_retry_at:-n/a} last_error=${last_error:-n/a}"
  sleep "$POLL_INTERVAL_SECONDS"
done

if [[ "${delivery_status:-missing}" != "succeeded" ]]; then
  echo "Timed out waiting for a successful delivery" >&2
  exit 1
fi

print_section "Verifying built-in receiver captured the request"
receiver_deadline=$((SECONDS + TIMEOUT_SECONDS))
captured_request_count=0
while (( SECONDS < receiver_deadline )); do
  captured_request_count="$(python3 - "$API_BASE_URL" "$receiver_id" "$event_id" <<'PY'
import json
import sys
import urllib.request

api_url = sys.argv[1]
receiver_id = sys.argv[2]
event_id = sys.argv[3]

with urllib.request.urlopen(f"{api_url}/test-webhooks/{receiver_id}/requests", timeout=10) as response:
    requests = json.loads(response.read().decode())

matches = 0
for item in requests:
    body = item.get("body")
    if isinstance(body, dict) and body.get("id") == event_id:
        matches += 1

print(matches)
PY
)"

  if [[ "$captured_request_count" -gt 0 ]]; then
    echo "Receiver captured $captured_request_count matching request(s)"
    break
  fi

  sleep "$POLL_INTERVAL_SECONDS"
done

if [[ "$captured_request_count" -lt 1 ]]; then
  echo "Built-in receiver did not capture the smoke event payload" >&2
  exit 1
fi

print_section "Smoke test succeeded"
echo "receiver_id=$receiver_id"
echo "endpoint_id=$endpoint_id"
echo "event_id=$event_id"
echo "delivery_id=$delivery_id"
