#!/usr/bin/env python3
"""
Surveille ~/BigData/logs et publie chaque NOUVELLE ligne dans Redpanda.

Topic : opencode.logs
Broker : localhost:19092

Au premier démarrage, le contenu historique déjà présent est ignoré.
Utiliser --from-start pour une relecture volontaire.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from confluent_kafka import Producer

PROJECT = Path(__file__).resolve().parent
DEFAULT_LOGS_DIR = PROJECT / "logs"

STATE_DIR = Path.home() / ".local" / "state" / "bigdata"
STATE_FILE = STATE_DIR / "redpanda-producer-offsets.json"


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def load_offsets() -> dict[str, int]:
    try:
        raw = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return {str(k): int(v) for k, v in raw.items()}
    except (FileNotFoundError, json.JSONDecodeError, ValueError, TypeError):
        return {}


def save_offsets(offsets: dict[str, int]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(offsets, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    tmp.replace(STATE_FILE)


def delivery_report(err, _msg) -> None:
    if err is not None:
        print(f"[REDPANDA] Livraison échouée : {err}", file=sys.stderr)


def iter_log_files(logs_dir: Path):
    for path in sorted(logs_dir.rglob("*")):
        if path.is_file() and not path.name.startswith("."):
            yield path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--broker",
        default=os.getenv("REDPANDA_BROKER", "localhost:19092"),
    )
    parser.add_argument(
        "--topic",
        default=os.getenv("REDPANDA_TOPIC", "opencode.logs"),
    )
    parser.add_argument(
        "--logs-dir",
        type=Path,
        default=Path(os.getenv("OPENCODE_LOGS_DIR", str(DEFAULT_LOGS_DIR))),
    )
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--from-start", action="store_true")
    args = parser.parse_args()

    args.logs_dir.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    producer = Producer(
        {
            "bootstrap.servers": args.broker,
            "client.id": "bigdata-opencode-producer",
            "acks": "all",
        }
    )

    offsets = load_offsets()
    running = True

    def stop_handler(_signum, _frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop_handler)
    signal.signal(signal.SIGINT, stop_handler)

    print(f"[REDPANDA] Broker : {args.broker}")
    print(f"[REDPANDA] Topic  : {args.topic}")
    print(f"[REDPANDA] Logs   : {args.logs_dir}")
    print("[REDPANDA] Surveillance active.")

    try:
        while running:
            changed = False

            for path in iter_log_files(args.logs_dir):
                key = str(path.resolve())

                try:
                    size = path.stat().st_size
                except FileNotFoundError:
                    continue

                if key not in offsets:
                    offsets[key] = 0 if args.from_start else size
                    changed = True

                # Cas d'un fichier tronqué / recréé.
                if size < offsets[key]:
                    offsets[key] = 0
                    changed = True

                if size == offsets[key]:
                    continue

                try:
                    with path.open("rb") as fh:
                        fh.seek(offsets[key])

                        while running:
                            raw = fh.readline()
                            if not raw:
                                break

                            offsets[key] = fh.tell()
                            changed = True

                            content = raw.decode(
                                "utf-8", errors="replace"
                            ).rstrip("\r\n")

                            if not content:
                                continue

                            try:
                                source_file = str(path.relative_to(args.logs_dir))
                            except ValueError:
                                source_file = path.name

                            event = {
                                "timestamp": now_utc(),
                                "session_id": os.getenv(
                                    "OPENCODE_SESSION_ID", "live"
                                ),
                                "type": "opencode_log",
                                "content": content,
                                "source_file": source_file,
                            }

                            producer.produce(
                                args.topic,
                                key=source_file.encode("utf-8"),
                                value=json.dumps(
                                    event,
                                    ensure_ascii=False,
                                ).encode("utf-8"),
                                callback=delivery_report,
                            )
                            producer.poll(0)

                except (OSError, PermissionError) as exc:
                    print(
                        f"[REDPANDA] Lecture impossible {path}: {exc}",
                        file=sys.stderr,
                    )

            if changed:
                save_offsets(offsets)

            producer.poll(0)
            time.sleep(args.interval)

    finally:
        save_offsets(offsets)
        remaining = producer.flush(10)
        if remaining:
            print(
                f"[REDPANDA] {remaining} message(s) encore en attente.",
                file=sys.stderr,
            )

    print("[REDPANDA] Producer arrêté.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
