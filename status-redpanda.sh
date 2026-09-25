#!/usr/bin/env bash
set -u

PROJECT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE="$HOME/.local/state/bigdata"
COMPOSE="$PROJECT/docker-compose.redpanda.yml"

check_pid() {
    local name="$1"
    local pidfile="$2"

    if [ -f "$pidfile" ]; then
        local pid
        pid="$(cat "$pidfile" 2>/dev/null || true)"
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            echo "✅ $name : actif (PID $pid)"
            return
        fi
    fi

    echo "❌ $name : arrêté"
}

echo "=== Docker / Redpanda ==="
docker compose -f "$COMPOSE" ps 2>/dev/null || true

echo ""
echo "=== Processus ==="
check_pid \
    "Producer Redpanda" \
    "$STATE/redpanda-producer.pid"

check_pid \
    "Spark Structured Streaming" \
    "$STATE/spark-redpanda.pid"

echo ""
echo "=== Topic ==="
if docker exec redpanda-0 rpk cluster health >/dev/null 2>&1; then
    docker exec redpanda-0 rpk topic list 2>/dev/null || true
else
    echo "Redpanda indisponible."
fi

echo ""
echo "Console : http://localhost:8080"
