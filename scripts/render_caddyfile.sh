#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE_FILE="$ROOT_DIR/Caddyfile.template"
OUTPUT_FILE="$ROOT_DIR/Caddyfile"

EVENTRELAY_HOST="${EVENTRELAY_HOST:-eventrelay.ddnsfree.com}"

if [[ ! -f "$TEMPLATE_FILE" ]]; then
  echo "Missing template: $TEMPLATE_FILE" >&2
  exit 1
fi

sed \
  -e "s/EVENTRELAY_HOST/${EVENTRELAY_HOST}/g" \
  "$TEMPLATE_FILE" > "$OUTPUT_FILE"

echo "Generated $OUTPUT_FILE"
echo "Public URL: https://${EVENTRELAY_HOST}"
