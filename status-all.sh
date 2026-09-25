#!/bin/bash

PROJECT="$HOME/BigData"


echo ""
echo "=========================================="
echo "          ETAT INFRA BIGDATA"
echo "=========================================="
echo ""


echo "RUSTFS / DOCKER"
echo "----------------"

cd "$PROJECT" || exit 1

if docker compose version >/dev/null 2>&1; then

    docker compose ps

else

    docker-compose ps

fi


echo ""
echo "SERVICES"
echo "--------"


if ss -ltn | grep -q ":9000"; then
    echo "🟢 RustFS S3       :9000"
else
    echo "🔴 RustFS S3       :9000"
fi


if ss -ltn | grep -q ":9001"; then
    echo "🟢 RustFS Console  :9001"
else
    echo "🔴 RustFS Console  :9001"
fi


if ss -ltn | grep -q ":8501"; then
    echo "🟢 Streamlit       :8501"
else
    echo "🔴 Streamlit       :8501"
fi


if pgrep -f "opencode serve" >/dev/null; then
    echo "🟢 OpenCode Serve"
else
    echo "🔴 OpenCode Serve"
fi


if pgrep -f "sync-opencode-log.sh" >/dev/null; then
    echo "🟢 Sync logs OpenCode"
else
    echo "🔴 Sync logs OpenCode"
fi


if pgrep -f "spark_dashboard_export.py" >/dev/null; then
    echo "🟠 Spark : traitement en cours"
else
    echo "⚪ Spark : aucun traitement en cours"
fi


echo ""
echo "DERNIER ETAT SPARK"
echo "------------------"

STATUS="$PROJECT/dashboard_cache/spark_status.json"

if [ -f "$STATUS" ]; then

    cat "$STATUS"

else

    echo "Aucun traitement Spark encore effectue."

fi


echo ""
# --- REDPANDA STATUS ---
echo ""
echo "========================================"
echo "  REDPANDA / STREAMING"
echo "========================================"
RP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -x "$RP_DIR/status-redpanda.sh" ]; then
    "$RP_DIR/status-redpanda.sh" || true
else
    echo "⚠️ status-redpanda.sh introuvable."
fi
# --- REDPANDA STATUS END ---
