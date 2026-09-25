#!/usr/bin/env bash
set -euo pipefail

PROJECT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$PROJECT/.venv/bin/python"

echo "[SETUP] Projet : $PROJECT"

if [ ! -x "$PYTHON" ]; then
    echo "ERREUR : environnement Python introuvable : $PROJECT/.venv"
    exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
    echo "ERREUR : Docker est introuvable."
    exit 1
fi

echo "[SETUP] Installation du client Python Redpanda/Kafka..."
"$PYTHON" -m pip install --upgrade confluent-kafka

echo "[SETUP] Vérification Python..."
"$PYTHON" -m py_compile \
    "$PROJECT/redpanda_producer.py" \
    "$PROJECT/spark_redpanda_stream.py"

echo "[SETUP] Vérification Docker Compose..."
docker compose \
    -f "$PROJECT/docker-compose.redpanda.yml" \
    config >/dev/null

chmod +x \
    "$PROJECT/setup-redpanda.sh" \
    "$PROJECT/start-redpanda.sh" \
    "$PROJECT/stop-redpanda.sh" \
    "$PROJECT/status-redpanda.sh" \
    "$PROJECT/send-redpanda-test.sh"

mkdir -p "$PROJECT/logs"
mkdir -p "$HOME/.local/state/bigdata"

echo ""
echo "Configuration Redpanda terminée."
echo "Démarrage : ./start-redpanda.sh"
