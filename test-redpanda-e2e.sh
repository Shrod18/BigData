#!/usr/bin/env bash
set -u
cd "$(dirname "${BASH_SOURCE[0]}")"
PREFIX="s3://opencode-data/spark-warehouse/opencode/logs_stream/"
count_parquet() {
  aws --profile rustfs --endpoint-url http://localhost:9000 s3 ls "$PREFIX" --recursive 2>/dev/null \
    | awk '/\/data\/.*\.parquet$/ {n++} END {print n+0}'
}
echo "=== État ==="
./status-redpanda.sh || exit 1
before="$(count_parquet)"
echo "Parquet avant : $before"
./send-redpanda-test.sh || exit 1
echo "Attente du micro-batch Spark..."
sleep 20
after="$(count_parquet)"
echo "Parquet après : $after"
grep -E '\[SPARK\]|ERROR|Exception' "$HOME/.local/state/bigdata/spark-redpanda.log" | tail -20 || true
if [ "$after" -gt "$before" ]; then
  echo "✅ TEST E2E OK : Redpanda → Spark → Iceberg → RustFS"
  exit 0
fi
echo "⚠️ Pas de nouveau Parquet détecté dans les 20 s."
exit 2
