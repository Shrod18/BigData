#!/bin/bash

PROJECT="$HOME/BigData"
LOGDIR="$PROJECT/logs"
BUCKET="s3://opencode-data"
ENDPOINT="http://localhost:9000"

mkdir -p "$LOGDIR"

while true
do
    cd "$PROJECT" || exit 1

    SESSION_ID=$(opencode session list \
        --max-count 1 \
        --format json | jq -r '.[0].id')

    if [ "$SESSION_ID" != "null" ] && [ -n "$SESSION_ID" ]; then

        LOGFILE="$LOGDIR/${SESSION_ID}.json"

        echo "$(date '+%Y-%m-%d %H:%M:%S') - export $SESSION_ID"

        opencode session export "$SESSION_ID" \
            --sanitize \
            > "$LOGFILE"

        aws --profile rustfs \
            --endpoint-url "$ENDPOINT" \
            s3 cp "$LOGFILE" \
            "$BUCKET/logs/$(basename "$LOGFILE")"
    fi

    sleep 10
done
