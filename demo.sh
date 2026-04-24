# 1. Create normal endpoint
curl -X POST http://localhost:8000/endpoints \
  -H "Content-Type: application/json" \
  -d '{
    "name": "normal-endpoint",
    "target_url": "http://host.docker.internal:9000/webhook",
    "simulation_latency_ms": 0,
    "simulation_failure_rate": 0,
    "simulation_timeout_rate": 0
  }'

# 2. Create simulated unstable endpoint
curl -X POST http://localhost:8000/endpoints \
  -H "Content-Type: application/json" \
  -d '{
    "name": "unstable-network-endpoint",
    "target_url": "http://host.docker.internal:9000/webhook",
    "simulation_latency_ms": 300,
    "simulation_failure_rate": 50,
    "simulation_timeout_rate": 0
  }'

# 3. Send test events
for i in {1..10}; do
  curl -X POST http://localhost:8000/events \
    -H "Content-Type: application/json" \
    -d "{\"event_type\":\"demo.network.test\",\"payload\":{\"i\":$i}}"
done