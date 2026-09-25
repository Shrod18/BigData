from __future__ import annotations
import json, os, socket, subprocess, time, uuid
from pathlib import Path
import pandas as pd
import streamlit as st

BROKER = os.environ.get("REDPANDA_BROKER", "localhost:19092")
TOPIC = os.environ.get("REDPANDA_TOPIC", "opencode.logs")
STATE = Path.home()/".local"/"state"/"bigdata"
S3_PREFIX = "s3://opencode-data/spark-warehouse/opencode/logs_stream/"

def pid_alive(name):
    try:
        pid = int((STATE/name).read_text().strip())
        os.kill(pid, 0)
        return True
    except Exception:
        return False

def broker_alive():
    host, port = BROKER.rsplit(":", 1)
    try:
        with socket.create_connection((host, int(port)), timeout=.8):
            return True
    except OSError:
        return False

def parquet_count():
    try:
        p = subprocess.run([
            "aws","--profile","rustfs","--endpoint-url","http://localhost:9000",
            "s3","ls",S3_PREFIX,"--recursive"
        ], capture_output=True, text=True, timeout=8)
        if p.returncode != 0: return None
        return sum("/data/" in x and x.rstrip().endswith(".parquet") for x in p.stdout.splitlines())
    except Exception:
        return None

def recent_messages(limit=30):
    cols = ["timestamp","session_id","type","content","source_file","offset"]
    try:
        from confluent_kafka import Consumer
    except Exception:
        return pd.DataFrame(columns=cols)
    c = Consumer({
        "bootstrap.servers": BROKER,
        "group.id": f"dashboard-{uuid.uuid4()}",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    })
    rows=[]
    try:
        c.subscribe([TOPIC])
        end=time.monotonic()+4
        idle=0
        while time.monotonic()<end and len(rows)<500:
            m=c.poll(.25)
            if m is None:
                if rows:
                    idle += 1
                    if idle >= 4: break
                continue
            if m.error(): continue
            idle=0
            try: d=json.loads(m.value().decode("utf-8"))
            except Exception: d={"content":m.value().decode("utf-8",errors="replace")}
            rows.append({
                "timestamp":d.get("timestamp",""), "session_id":d.get("session_id",""),
                "type":d.get("type",""), "content":d.get("content",""),
                "source_file":d.get("source_file",""), "offset":m.offset()
            })
    finally:
        c.close()
    return pd.DataFrame(rows[-limit:], columns=cols)

def render_redpanda_panel():
    with st.expander("🔴 Redpanda / Streaming temps réel", expanded=False):
        c1,c2,c3,c4=st.columns(4)
        c1.metric("Broker", "Actif" if broker_alive() else "Arrêté")
        c2.metric("Producer", "Actif" if pid_alive("redpanda-producer.pid") else "Arrêté")
        c3.metric("Spark Streaming", "Actif" if pid_alive("spark-redpanda.pid") else "Arrêté")
        n=parquet_count()
        c4.metric("Parquet", n if n is not None else "—")
        st.caption("Redpanda → Spark Structured Streaming → Iceberg → Parquet → RustFS")
        if st.button("Actualiser les messages Redpanda", key="redpanda_refresh"):
            st.session_state["redpanda_recent"] = recent_messages()
        df=st.session_state.get("redpanda_recent")
        if isinstance(df,pd.DataFrame):
            if df.empty: st.info("Aucun message disponible.")
            else: st.dataframe(df.iloc[::-1], use_container_width=True, hide_index=True)
        else:
            st.info("Clique sur le bouton pour lire les derniers messages de opencode.logs.")
        st.code("./send-redpanda-test.sh", language="bash")
        st.caption("Console Redpanda : http://localhost:8080")
