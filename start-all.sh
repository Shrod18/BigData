#!/bin/bash

PROJECT="$HOME/BigData"
STATE="$HOME/.local/state/bigdata"

mkdir -p "$STATE"

cd "$PROJECT" || exit 1


echo ""
echo "=========================================="
echo "       DEMARRAGE INFRA BIGDATA"
echo "=========================================="
echo ""


# ============================================================
# 1/8 - PYTHON
# ============================================================

echo "[1/8] Environnement Python..."

if [ ! -f "$PROJECT/.venv/bin/activate" ]; then
    echo "ERREUR : .venv introuvable."
    exit 1
fi

source "$PROJECT/.venv/bin/activate"

PYTHON="$PROJECT/.venv/bin/python"

echo "$($PYTHON --version)"


# ============================================================
# 2/8 - RUSTFS
# ============================================================

echo ""
echo "[2/8] RustFS..."

if docker compose version >/dev/null 2>&1; then
    docker compose up -d
else
    docker-compose up -d
fi

echo "Attente de RustFS..."

for i in {1..20}
do
    if curl -s \
        -o /dev/null \
        http://127.0.0.1:9000
    then
        echo "RustFS operationnel."
        break
    fi

    sleep 1
done


# ============================================================
# 3/8 - OPENCODE
# ============================================================

echo ""
echo "[3/8] OpenCode..."

OPENCODE_BIN="$(
    command -v opencode 2>/dev/null || true
)"

if [ -z "$OPENCODE_BIN" ] \
   && [ -x "$HOME/.opencode/bin/opencode" ]
then
    OPENCODE_BIN="$HOME/.opencode/bin/opencode"
fi

if [ -n "$OPENCODE_BIN" ]; then

    if pgrep -f "opencode serve" >/dev/null; then
        echo "OpenCode deja actif."
    else
        nohup "$OPENCODE_BIN" serve \
            > "$STATE/opencode.log" \
            2>&1 &

        echo $! > "$STATE/opencode.pid"

        echo "OpenCode demarre."
    fi

else
    echo "OpenCode introuvable."
fi


# ============================================================
# 4/8 - SYNC LOGS
# ============================================================

echo ""
echo "[4/8] Synchronisation logs..."

if [ -f "$PROJECT/sync-opencode-log.sh" ]; then

    chmod +x "$PROJECT/sync-opencode-log.sh"

    if pgrep -f "sync-opencode-log.sh" >/dev/null; then
        echo "Sync logs deja active."
    else
        nohup "$PROJECT/sync-opencode-log.sh" \
            > "$STATE/opencode-sync.log" \
            2>&1 &

        echo $! > "$STATE/opencode-sync.pid"

        echo "Sync logs demarree."
    fi

else
    echo "Script sync logs introuvable."
fi


# ============================================================
# 5/8 - SYNC FICHIERS S3
# ============================================================

echo ""
echo "[5/8] Synchronisation fichiers..."

SYNC_SCRIPT=""

if [ -f "$PROJECT/sync-opencode-s3.sh" ]; then

    SYNC_SCRIPT="$PROJECT/sync-opencode-s3.sh"

elif [ -f "$HOME/sync-opencode-s3.sh" ]; then

    SYNC_SCRIPT="$HOME/sync-opencode-s3.sh"

fi

if [ -n "$SYNC_SCRIPT" ]; then

    chmod +x "$SYNC_SCRIPT"

    if pgrep -f "sync-opencode-s3.sh" >/dev/null; then
        echo "Sync S3 deja active."
    else
        nohup "$SYNC_SCRIPT" \
            > "$STATE/s3-sync.log" \
            2>&1 &

        echo $! > "$STATE/s3-sync.pid"

        echo "Sync S3 demarree."
    fi

else
    echo "Aucun script sync S3."
fi


# ============================================================
# 6/8 - STREAMLIT
# ============================================================

echo ""
echo "[6/8] Dashboard Streamlit..."

if ss -ltn | grep -q ':8501'; then

    echo "Dashboard deja actif."

else

    nohup "$PYTHON" \
        -m streamlit run \
        "$PROJECT/dashboard.py" \
        --server.headless true \
        --server.fileWatcherType none \
        > "$STATE/streamlit.log" \
        2>&1 &

    echo $! > "$STATE/streamlit.pid"

    echo "Dashboard demarre."
fi


# ============================================================
# 7/8 - DOCSIFY
# ============================================================

echo ""
echo "[7/8] Documentation Docsify..."

if [ ! -f "$PROJECT/docs/index.html" ]; then

    echo "ERREUR : docs/index.html introuvable."

elif ss -ltn | grep -q ':3000'; then

    echo "Docsify deja actif."

else

    nohup "$PYTHON" \
        -m http.server 3000 \
        --directory "$PROJECT/docs" \
        > "$STATE/docsify.log" \
        2>&1 &

    echo $! > "$STATE/docsify.pid"

    echo "Docsify demarre."
fi


# ============================================================
# 8/8 - INVENTAIRE RUSTFS
# ============================================================

echo ""
echo "[8/8] Inventaire RustFS..."

if pgrep -f "rustfs_dashboard_export.py" >/dev/null; then

    echo "Inventaire RustFS deja en cours."

else

    nohup "$PYTHON" \
        "$PROJECT/rustfs_dashboard_export.py" \
        > "$STATE/rustfs-export.log" \
        2>&1 &

    echo $! > "$STATE/rustfs-export.pid"

    echo "Inventaire RustFS lance en arriere-plan."
fi


# ============================================================
# FIN
# ============================================================

echo ""
echo "=========================================="
echo "        INFRA BIGDATA DEMARREE"
echo "=========================================="
echo ""

echo "Dashboard Streamlit :"
echo "  http://localhost:8501"

echo ""

echo "Documentation Docsify :"
echo "  http://localhost:3000"

echo ""

echo "RustFS :"
echo "  http://localhost:9001"

echo ""

echo "API S3 RustFS :"
echo "  http://localhost:9000"

echo ""

echo "Spark :"
echo "  lancement manuel depuis le dashboard"

echo ""

echo "Logs :"
echo "  $STATE"

echo ""