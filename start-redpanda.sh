#!/usr/bin/env bash

export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH="$JAVA_HOME/bin:$PATH"

set -euo pipefail

PROJECT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE="$HOME/.local/state/bigdata"
PYTHON="$PROJECT/.venv-spark35/bin/python"
COMPOSE="$PROJECT/docker-compose.redpanda.yml"

BROKER="${REDPANDA_BROKER:-localhost:19092}"
TOPIC="${REDPANDA_TOPIC:-opencode.logs}"

mkdir -p "$STATE" "$PROJECT/logs"

if [ ! -x "$PYTHON" ]; then
    echo "ERREUR : $PROJECT/.venv-spark35/bin/python introuvable."
    exit 1
fi

if ! "$PYTHON" -c "import confluent_kafka" >/dev/null 2>&1; then
    echo "ERREUR : confluent-kafka n'est pas installé."
    echo "Lance d'abord : ./setup-redpanda.sh"
    exit 1
fi

echo "[REDPANDA] Démarrage du broker et de la console..."
docker compose -f "$COMPOSE" up -d

echo "[REDPANDA] Attente du broker..."
ready=0
for _ in $(seq 1 40); do
    if docker exec redpanda-0 rpk cluster health >/dev/null 2>&1; then
        ready=1
        break
    fi
    sleep 1
done

if [ "$ready" -ne 1 ]; then
    echo "ERREUR : Redpanda n'est pas prêt."
    docker compose -f "$COMPOSE" ps
    exit 1
fi

if ! docker exec redpanda-0 rpk topic list 2>/dev/null \
    | awk 'NR>1 {print $1}' \
    | grep -qx "$TOPIC"; then
    echo "[REDPANDA] Création du topic $TOPIC..."
    docker exec redpanda-0 \
        rpk topic create "$TOPIC" \
        --partitions 1 \
        --replicas 1
else
    echo "[REDPANDA] Topic $TOPIC déjà présent."
fi

start_bg() {
    local name="$1"
    local pidfile="$2"
    local logfile="$3"
    shift 3

    if [ -f "$pidfile" ] \
       && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
        echo "[$name] Déjà actif (PID $(cat "$pidfile"))."
        return
    fi

    nohup "$@" >"$logfile" 2>&1 &
    echo $! >"$pidfile"
    echo "[$name] Démarré (PID $!)."
}

start_bg \
    "PRODUCER" \
    "$STATE/redpanda-producer.pid" \
    "$STATE/redpanda-producer.log" \
    "$PYTHON" "$PROJECT/redpanda_producer.py" \
    --broker "$BROKER" \
    --topic "$TOPIC" \
    --logs-dir "$PROJECT/logs"

start_bg \
    "SPARK-STREAM" \
    "$STATE/spark-redpanda.pid" \
    "$STATE/spark-redpanda.log" \
    env \
    PYTHONUNBUFFERED=1 \
    SPARK_LOCAL_IP=127.0.0.1 \
    REDPANDA_BROKER="$BROKER" \
    REDPANDA_TOPIC="$TOPIC" \
    "$PYTHON" "$PROJECT/spark_redpanda_stream.py"

echo ""
echo "Redpanda est lancé."
echo ""
echo "Kafka API       : localhost:19092"
echo "Console         : http://localhost:8080"
echo "Schema Registry : http://localhost:18081"
echo "Admin API       : http://localhost:19644"
echo "Topic           : $TOPIC"
echo ""
echo "Logs :"
echo "  tail -f $STATE/redpanda-producer.log"
echo "  tail -f $STATE/spark-redpanda.log"
