#!/usr/bin/env bash
set -euo pipefail

TOPIC="${REDPANDA_TOPIC:-opencode.logs}"

payload="$(
python3 - <<'PY'
import json
from datetime import datetime, timezone

print(json.dumps({
    "timestamp": datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S.%f"
    )[:-3],
    "session_id": "test",
    "type": "test",
    "content": "Message de test Redpanda -> Spark -> Iceberg",
    "source_file": "send-redpanda-test.sh",
}, ensure_ascii=False))
PY
)"

printf '%s\n' "$payload" \
  | docker exec -i redpanda-0 \
      rpk topic produce "$TOPIC"

echo "Message envoyé dans $TOPIC"
