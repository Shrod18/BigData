#!/bin/bash

PROJECT="$HOME/BigData"
STATE="$HOME/.local/state/bigdata"


echo ""
echo "=========================================="
echo "        ARRET INFRA BIGDATA"
echo "=========================================="
echo ""


# ============================================================
# STREAMLIT
# ============================================================

echo "Arret Streamlit..."

pkill -f "streamlit run.*dashboard.py" \
    2>/dev/null || true


# ============================================================
# OPENCODE
# ============================================================

echo "Arret OpenCode..."

pkill -f "opencode serve" \
    2>/dev/null || true


# ============================================================
# SYNCHRONISATIONS
# ============================================================

echo "Arret synchronisations..."

pkill -f "sync-opencode-log.sh" \
    2>/dev/null || true

pkill -f "sync-opencode-s3.sh" \
    2>/dev/null || true


# ============================================================
# SPARK BATCH
# ============================================================

echo "Arret job Spark / Rustfs eventuel..."

pkill -f "spark_dashboard_export.py" \
    2>/dev/null || true
pkill -f "rustfs_dashboard_export.py" \
    2>/dev/null || true

# ============================================================
# RUSTFS
# ============================================================

echo "Arret RustFS..."

cd "$PROJECT" || exit 1

if docker compose version >/dev/null 2>&1; then

    docker compose down

else

    docker-compose down

fi

# ============================================================
# DOCSIFY
# ============================================================

echo ""
echo "Arrêt de Docsify..."

DOCSIFY_PID="$STATE/docsify.pid"

if [ -f "$DOCSIFY_PID" ]; then

    PID=$(cat "$DOCSIFY_PID")

    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID" 2>/dev/null
        echo "Docsify arrêté."
    else
        echo "Docsify n'était plus actif."
    fi

    rm -f "$DOCSIFY_PID"

else

    # Sécurité si le fichier PID n'existe plus
    pkill -f "http.server 3000" 2>/dev/null || true

    echo "Docsify arrêté si présent."
fi

# ============================================================
# PID
# ============================================================

rm -f \
    "$STATE/streamlit.pid" \
    "$STATE/opencode.pid" \
    "$STATE/opencode-sync.pid" \
    "$STATE/s3-sync.pid" \
    "$STATE/spark-export.pid"


echo ""
echo "Infrastructure BigData arretee."
echo ""
