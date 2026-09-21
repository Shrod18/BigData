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
# 1/7 - PYTHON
# ============================================================

echo "[1/7] Environnement Python..."


if [ ! -f "$PROJECT/.venv/bin/activate" ]; then

    echo "ERREUR : .venv introuvable."

    exit 1

fi


source "$PROJECT/.venv/bin/activate"


PYTHON="$PROJECT/.venv/bin/python"


echo "$($PYTHON --version)"


# ============================================================
# 2/7 - RUSTFS
# ============================================================

echo ""
echo "[2/7] RustFS..."


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
# 3/7 - OPENCODE
# ============================================================

echo ""
echo "[3/7] OpenCode..."


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


        echo $! \
            > "$STATE/opencode.pid"


        echo "OpenCode demarre."

    fi

else

    echo "OpenCode introuvable."

fi


# ============================================================
# 4/7 - SYNC LOGS
# ============================================================

echo ""
echo "[4/7] Synchronisation logs..."


if [ -f "$PROJECT/sync-opencode-log.sh" ]; then

    chmod +x \
        "$PROJECT/sync-opencode-log.sh"


    if pgrep -f \
        "sync-opencode-log.sh" \
        >/dev/null
    then

        echo "Sync logs deja active."

    else

        nohup \
            "$PROJECT/sync-opencode-log.sh" \
            > "$STATE/opencode-sync.log" \
            2>&1 &


        echo $! \
            > "$STATE/opencode-sync.pid"


        echo "Sync logs demarree."

    fi

fi


# ============================================================
# 5/7 - SYNC FICHIERS
# ============================================================

echo ""
echo "[5/7] Synchronisation fichiers..."


SYNC_SCRIPT=""


if [ -f "$PROJECT/sync-opencode-s3.sh" ]; then

    SYNC_SCRIPT="$PROJECT/sync-opencode-s3.sh"

elif [ -f "$HOME/sync-opencode-s3.sh" ]; then

    SYNC_SCRIPT="$HOME/sync-opencode-s3.sh"

fi


if [ -n "$SYNC_SCRIPT" ]; then

    chmod +x \
        "$SYNC_SCRIPT"


    if pgrep -f \
        "sync-opencode-s3.sh" \
        >/dev/null
    then

        echo "Sync S3 deja active."

    else

        nohup "$SYNC_SCRIPT" \
            > "$STATE/s3-sync.log" \
            2>&1 &


        echo $! \
            > "$STATE/s3-sync.pid"


        echo "Sync S3 demarree."

    fi

else

    echo "Aucun script sync S3."

fi


# ============================================================
# 6/7 - STREAMLIT
# ============================================================

echo ""
echo "[6/7] Dashboard..."


if ss -ltn \
    | grep -q ':8501'
then

    echo "Dashboard deja actif."

else

    nohup "$PYTHON" \
        -m streamlit run \
        "$PROJECT/dashboard.py" \
        --server.headless true \
        --server.fileWatcherType none \
        > "$STATE/streamlit.log" \
        2>&1 &


    echo $! \
        > "$STATE/streamlit.pid"


    echo "Dashboard demarre."

fi


# ============================================================
# 7/7 - INVENTAIRE RUSTFS
#
# Lancement EN ARRIERE-PLAN.
#
# Le dashboard n'attend PAS la fin.
# ============================================================

echo ""
echo "[7/7] Inventaire RustFS..."


if pgrep -f \
    "rustfs_dashboard_export.py" \
    >/dev/null
then

    echo "Inventaire RustFS deja en cours."

else

    nohup "$PYTHON" \
        "$PROJECT/rustfs_dashboard_export.py" \
        > "$STATE/rustfs-export.log" \
        2>&1 &


    echo $! \
        > "$STATE/rustfs-export.pid"


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

echo "Dashboard :"
echo "  http://localhost:8501"

echo ""

echo "RustFS :"
echo "  http://localhost:9001"

echo ""

echo "Spark :"
echo "  lancement manuel depuis le dashboard"

echo ""

echo "Inventaire RustFS :"
echo "  fonctionne en arriere-plan"

echo ""

echo "Logs :"
echo "  $STATE"

echo ""
