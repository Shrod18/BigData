#!/usr/bin/env bash
set -u

PROJECT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE="$HOME/.local/state/bigdata"
COMPOSE="$PROJECT/docker-compose.redpanda.yml"

stop_pid() {
    local name="$1"
    local pidfile="$2"

    if [ ! -f "$pidfile" ]; then
        echo "[$name] Aucun PID enregistré."
        return
    fi

    local pid
    pid="$(cat "$pidfile" 2>/dev/null || true)"

    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        echo "[$name] Arrêt du PID $pid..."
        kill "$pid" 2>/dev/null || true

        for _ in $(seq 1 10); do
            kill -0 "$pid" 2>/dev/null || break
            sleep 1
        done

        if kill -0 "$pid" 2>/dev/null; then
            kill -9 "$pid" 2>/dev/null || true
        fi
    else
        echo "[$name] Déjà arrêté."
    fi

    rm -f "$pidfile"
}

stop_pid "SPARK-STREAM" "$STATE/spark-redpanda.pid"
stop_pid "PRODUCER" "$STATE/redpanda-producer.pid"

echo "[REDPANDA] Arrêt Docker..."
docker compose -f "$COMPOSE" down

echo "Redpanda arrêté."
echo "Le volume redpanda-data est conservé."
