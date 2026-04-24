# EventRelay Network Proxy

This service sits between the EventRelay worker and the final webhook endpoint so we can simulate network conditions during local development.

## Endpoint

- `POST /proxy`

## Required Header

- `X-EventRelay-Target-Url`

## Optional Simulation Headers

- `X-EventRelay-Latency-Ms`
- `X-EventRelay-Timeout-Rate`
- `X-EventRelay-Failure-Rate`

## Behavior

- Adds optional latency before forwarding.
- Can inject synthetic timeouts by sleeping longer than the worker timeout.
- Can inject synthetic `503` failures without forwarding.
- Otherwise forwards the original JSON body and relevant signature headers to the target URL.

## Logs

Each request logs:

- target URL
- latency applied
- whether timeout or failure injection happened
- final response status
