import streamlit as st
import boto3
import pandas as pd
from datetime import datetime

# -------------------------
# Configuration RustFS
# -------------------------

ENDPOINT = "http://localhost:9000"
ACCESS_KEY = "rustfsadmin"
SECRET_KEY = "rustfsadmin"
BUCKET = "opencode-data"

s3 = boto3.client(
    "s3",
    endpoint_url=ENDPOINT,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name="us-east-1"
)

# -------------------------
# Interface
# -------------------------

st.set_page_config(
    page_title="OpenCode / RustFS Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 OpenCode / RustFS Dashboard")

st.caption(
    f"Bucket : {BUCKET} | RustFS : {ENDPOINT}"
)

# -------------------------
# Récupération des objets
# -------------------------

try:
    response = s3.list_objects_v2(Bucket=BUCKET)

    objects = response.get("Contents", [])

except Exception as e:
    st.error(f"Erreur de connexion à RustFS : {e}")
    st.stop()

# -------------------------
# Statistiques
# -------------------------

nb_files = len(objects)
total_size = sum(obj["Size"] for obj in objects)

total_mb = total_size / (1024 * 1024)

logs = [
    obj for obj in objects
    if obj["Key"].startswith("logs/")
]

col1, col2, col3 = st.columns(3)

col1.metric(
    "Nombre de fichiers",
    nb_files
)

col2.metric(
    "Stockage utilisé",
    f"{total_mb:.2f} MB"
)

col3.metric(
    "Logs OpenCode",
    len(logs)
)

# -------------------------
# Tableau des fichiers
# -------------------------

st.subheader("📁 Fichiers stockés")

if objects:

    data = []

    for obj in objects:

        data.append({
            "Fichier": obj["Key"],
            "Taille (KB)": round(obj["Size"] / 1024, 2),
            "Dernière modification": obj["LastModified"]
        })

    df = pd.DataFrame(data)

    df = df.sort_values(
        by="Dernière modification",
        ascending=False
    )

    st.dataframe(
        df,
        use_container_width=True
    )

else:

    st.info("Aucun fichier dans le bucket.")

# -------------------------
# Logs OpenCode
# -------------------------

st.subheader("🤖 Logs OpenCode")

if logs:

    for log in sorted(
        logs,
        key=lambda x: x["LastModified"],
        reverse=True
    )[:10]:

        st.write(
            f"📄 {log['Key']} "
            f"— {round(log['Size']/1024, 2)} KB "
            f"— {log['LastModified']}"
        )

else:

    st.info("Aucun log OpenCode trouvé.")

# -------------------------
# Dernière mise à jour
# -------------------------

st.divider()

st.write(
    "Dernière actualisation :",
    datetime.now().strftime("%d/%m/%Y %H:%M:%S")
)

if st.button("🔄 Actualiser"):
    st.rerun()
