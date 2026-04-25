#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE_FILE="$ROOT_DIR/Caddyfile.template"
OUTPUT_FILE="$ROOT_DIR/Caddyfile"

if [[ -z "${EC2_PUBLIC_IP:-}" ]]; then
  echo "EC2_PUBLIC_IP is required, for example: EC2_PUBLIC_IP=1.2.3.4 $0" >&2
  exit 1
fi

ip_dashed="${EC2_PUBLIC_IP//./-}"
EVENTRELAY_HOST="eventrelay.${ip_dashed}.sslip.io"
API_HOST="api.eventrelay.${ip_dashed}.sslip.io"

if [[ ! -f "$TEMPLATE_FILE" ]]; then
  echo "Missing template: $TEMPLATE_FILE" >&2
  exit 1
fi

sed \
  -e "s/EVENTRELAY_HOST/${EVENTRELAY_HOST}/g" \
  -e "s/API_HOST/${API_HOST}/g" \
  "$TEMPLATE_FILE" > "$OUTPUT_FILE"

echo "Generated $OUTPUT_FILE"
echo "Frontend URL: https://${EVENTRELAY_HOST}"
echo "API URL: https://${API_HOST}"
