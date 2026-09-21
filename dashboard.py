import json
import os
import subprocess
import sys

from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_DIR = (
    Path.home()
    / "BigData"
)

STATE_DIR = (
    Path.home()
    / ".local"
    / "state"
    / "bigdata"
)

CACHE_DIR = (
    STATE_DIR
    / "dashboard_cache"
)

STATE_DIR.mkdir(
    parents=True,
    exist_ok=True
)

CACHE_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# RUSTFS CACHE
# ============================================================

RUSTFS_SCRIPT = (
    PROJECT_DIR
    / "rustfs_dashboard_export.py"
)

RUSTFS_PID_FILE = (
    STATE_DIR
    / "rustfs-export.pid"
)

RUSTFS_LOG_FILE = (
    STATE_DIR
    / "rustfs-export.log"
)

RUSTFS_STATUS_FILE = (
    CACHE_DIR
    / "rustfs_status.json"
)

RUSTFS_SUMMARY_FILE = (
    CACHE_DIR
    / "rustfs_summary.json"
)

RUSTFS_RECENT_FILE = (
    CACHE_DIR
    / "rustfs_recent.csv"
)

RUSTFS_LOGS_FILE = (
    CACHE_DIR
    / "rustfs_logs.csv"
)


# ============================================================
# SPARK CACHE
# ============================================================

SPARK_SCRIPT = (
    PROJECT_DIR
    / "spark_dashboard_export.py"
)

SPARK_PID_FILE = (
    STATE_DIR
    / "spark-export.pid"
)

SPARK_LOG_FILE = (
    STATE_DIR
    / "spark-export.log"
)

SPARK_STATUS_FILE = (
    CACHE_DIR
    / "spark_status.json"
)

ICEBERG_ROWS_FILE = (
    CACHE_DIR
    / "iceberg_rows.csv"
)

SNAPSHOTS_FILE = (
    CACHE_DIR
    / "snapshots.csv"
)

SPARK_STATS_FILE = (
    CACHE_DIR
    / "spark_stats.csv"
)

SPARK_ACTIVITY_FILE = (
    CACHE_DIR
    / "spark_activity.csv"
)


# ============================================================
# STREAMLIT
# ============================================================

st.set_page_config(
    page_title=(
        "Big Data Control Center"
    ),
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# STYLE
# ============================================================

st.markdown(
    """
    <style>

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
    }

    div[data-testid="stMetric"] {
        border: 1px solid rgba(128,128,128,0.20);
        padding: 12px;
        border-radius: 12px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# OUTILS
# ============================================================

def human_size(
    size_bytes
):

    size_bytes = int(
        size_bytes
    )

    if size_bytes < 1024:
        return f"{size_bytes} B"

    if size_bytes < 1024 ** 2:

        return (
            f"{size_bytes / 1024:.2f} KB"
        )

    if size_bytes < 1024 ** 3:

        return (
            f"{size_bytes / 1024**2:.2f} MB"
        )

    return (
        f"{size_bytes / 1024**3:.2f} GB"
    )


def load_json(
    path
):

    if not path.exists():
        return {}

    try:

        return json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except Exception:

        return {}


@st.cache_data(
    ttl=30,
    show_spinner=False
)
def load_csv(
    path_string
):

    path = Path(
        path_string
    )

    if not path.exists():

        return pd.DataFrame()


    try:

        return pd.read_csv(
            path
        )

    except Exception:

        return pd.DataFrame()


# ============================================================
# PROCESSUS BACKGROUND
# ============================================================

def process_running(
    pid_file
):

    if not pid_file.exists():
        return False


    try:

        pid = int(
            pid_file
            .read_text()
            .strip()
        )


        os.kill(
            pid,
            0
        )

        return True


    except Exception:

        try:

            pid_file.unlink(
                missing_ok=True
            )

        except Exception:
            pass


        return False


def start_background_job(
    script,
    pid_file,
    log_file
):

    if process_running(
        pid_file
    ):

        return False


    if not script.exists():

        raise FileNotFoundError(
            str(
                script
            )
        )


    logfile = open(
        log_file,
        "ab"
    )


    process = subprocess.Popen(
        [
            sys.executable,
            str(
                script
            )
        ],

        cwd=str(
            PROJECT_DIR
        ),

        stdout=logfile,

        stderr=subprocess.STDOUT,

        start_new_session=True
    )


    pid_file.write_text(
        str(
            process.pid
        )
    )


    return True


def read_log(
    path,
    lines=80
):

    if not path.exists():

        return ""


    try:

        content = (
            path
            .read_text(
                encoding="utf-8",
                errors="replace"
            )
            .splitlines()
        )


        return "\n".join(
            content[
                -lines:
            ]
        )


    except Exception:

        return ""


# ============================================================
# ETATS
# ============================================================

rustfs_running = (
    process_running(
        RUSTFS_PID_FILE
    )
)

spark_running = (
    process_running(
        SPARK_PID_FILE
    )
)


rustfs_status = load_json(
    RUSTFS_STATUS_FILE
)

rustfs_summary = load_json(
    RUSTFS_SUMMARY_FILE
)

spark_status = load_json(
    SPARK_STATUS_FILE
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title(
    "⚙️ Big Data"
)


page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Vue générale",
        "📦 Stockage S3",
        "🧊 Iceberg",
        "⚡ Spark",
        "🤖 OpenCode"
    ]
)


st.sidebar.divider()


# ============================================================
# ACTUALISER AFFICHAGE
# ============================================================

if st.sidebar.button(
    "🔄 Actualiser l'affichage"
):

    load_csv.clear()

    st.rerun()


# ============================================================
# RUSTFS
# ============================================================

if rustfs_running:

    st.sidebar.warning(
        "📦 Inventaire RustFS en cours..."
    )

else:

    if st.sidebar.button(
        "📦 Actualiser RustFS"
    ):

        try:

            start_background_job(
                RUSTFS_SCRIPT,
                RUSTFS_PID_FILE,
                RUSTFS_LOG_FILE
            )

            st.sidebar.success(
                "Inventaire RustFS lancé."
            )

            st.rerun()

        except Exception as e:

            st.sidebar.error(
                str(e)
            )


# ============================================================
# SPARK
# ============================================================

if spark_running:

    st.sidebar.warning(
        "⚡ Spark travaille..."
    )

else:

    if st.sidebar.button(
        "⚡ Actualiser Spark / Iceberg"
    ):

        try:

            start_background_job(
                SPARK_SCRIPT,
                SPARK_PID_FILE,
                SPARK_LOG_FILE
            )

            st.sidebar.success(
                "Traitement Spark lancé."
            )

            st.rerun()

        except Exception as e:

            st.sidebar.error(
                str(e)
            )


st.sidebar.divider()


if rustfs_summary:

    st.sidebar.caption(
        "Inventaire RustFS : "
        + rustfs_summary.get(
            "generated_at",
            "inconnu"
        )
    )


if spark_status:

    st.sidebar.caption(
        "Dernier Spark : "
        + spark_status.get(
            "updated_at",
            "inconnu"
        )
    )


# ============================================================
# TITRE
# ============================================================

st.title(
    "📊 Big Data Control Center"
)

st.caption(
    "OpenCode · RustFS · Apache Spark · "
    "Apache Iceberg · Streamlit"
)


# ============================================================
# PAGE ACCUEIL
# ============================================================

if page == "🏠 Vue générale":

    st.header(
        "Vue générale"
    )


    # ========================================================
    # ETAT
    # ========================================================

    c1, c2, c3 = (
        st.columns(3)
    )


    with c1:

        if rustfs_running:

            st.warning(
                "🟠 RustFS : inventaire en cours"
            )

        elif (
            rustfs_status.get(
                "status"
            )
            == "success"
        ):

            st.success(
                "🟢 RustFS opérationnel"
            )

        elif (
            rustfs_status.get(
                "status"
            )
            == "error"
        ):

            st.error(
                "🔴 RustFS en erreur"
            )

        else:

            st.info(
                "⚪ RustFS : aucun inventaire"
            )


    with c2:

        if spark_running:

            st.warning(
                "🟠 Spark travaille"
            )

        elif (
            spark_status.get(
                "status"
            )
            == "success"
        ):

            st.success(
                "🟢 Spark opérationnel"
            )

        elif (
            spark_status.get(
                "status"
            )
            == "error"
        ):

            st.error(
                "🔴 Spark en erreur"
            )

        else:

            st.info(
                "⚪ Spark en attente"
            )


    with c3:

        if (
            spark_status.get(
                "status"
            )
            == "success"
        ):

            st.success(
                "🟢 Iceberg opérationnel"
            )

        else:

            st.info(
                "⚪ Iceberg en attente"
            )


    # ========================================================
    # PAS ENCORE DE CACHE RUSTFS
    # ========================================================

    if not rustfs_summary:

        st.info(
            "Aucun inventaire RustFS disponible pour le moment."
        )

        st.write(
            "Clique sur **📦 Actualiser RustFS** dans "
            "le menu. Le scan se fera en arrière-plan."
        )


    else:

        # ====================================================
        # KPI
        # ====================================================

        k1, k2, k3, k4, k5 = (
            st.columns(5)
        )


        k1.metric(
            "Objets S3",
            rustfs_summary.get(
                "total_objects",
                0
            )
        )


        k2.metric(
            "Volume",
            human_size(
                rustfs_summary.get(
                    "total_size",
                    0
                )
            )
        )


        k3.metric(
            "Logs OpenCode",
            rustfs_summary.get(
                "logs_count",
                0
            )
        )


        k4.metric(
            "Objets Iceberg",
            rustfs_summary.get(
                "iceberg_objects",
                0
            )
        )


        k5.metric(
            "Lignes Iceberg",
            spark_status.get(
                "total_rows",
                "-"
            )
        )


        st.divider()


        # ====================================================
        # GRAPHIQUES
        # ====================================================

        graph1, graph2 = (
            st.columns(2)
        )


        with graph1:

            st.subheader(
                "Répartition du stockage"
            )


            categories = (
                rustfs_summary.get(
                    "category_counts",
                    {}
                )
            )


            if categories:

                category_series = pd.Series(
                    categories,
                    name="Objets"
                )


                st.bar_chart(
                    category_series
                )


        with graph2:

            st.subheader(
                "Activité du stockage"
            )


            activity = (
                rustfs_summary.get(
                    "daily_activity",
                    {}
                )
            )


            if activity:

                activity_series = (
                    pd.Series(
                        activity,
                        name="Objets"
                    )
                )


                activity_series.index = (
                    pd.to_datetime(
                        activity_series.index
                    )
                )


                st.line_chart(
                    activity_series
                )


    # ========================================================
    # ARCHITECTURE
    # ========================================================

    st.subheader(
        "🏗️ Architecture"
    )


    st.code(
        """
OpenCode
   │
   ▼
~/BigData
   │
   ▼
RustFS S3
   │
   ├──────────────┐
   │              │
   ▼              ▼
Fichiers      Apache Spark
                  │
                  ▼
             Apache Iceberg
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
     Parquet   Metadata  Snapshots
                  │
                  ▼
               RustFS
                  │
                  ▼
      Cache statistiques local
                  │
                  ▼
              Streamlit
"""
    )


# ============================================================
# STOCKAGE S3
# ============================================================

elif page == "📦 Stockage S3":

    st.header(
        "📦 Stockage RustFS / S3"
    )


    if not rustfs_summary:

        st.info(
            "Lance d'abord un inventaire RustFS."
        )


    else:

        # ====================================================
        # KPI
        # ====================================================

        c1, c2 = (
            st.columns(2)
        )


        c1.metric(
            "Objets",
            rustfs_summary.get(
                "total_objects",
                0
            )
        )


        c2.metric(
            "Volume",
            human_size(
                rustfs_summary.get(
                    "total_size",
                    0
                )
            )
        )


        # ====================================================
        # EXTENSIONS
        # ====================================================

        st.subheader(
            "Types de fichiers"
        )


        extension_counts = (
            rustfs_summary.get(
                "extension_counts",
                {}
            )
        )


        if extension_counts:

            extension_series = (
                pd.Series(
                    extension_counts,
                    name="Nombre"
                )
                .sort_values(
                    ascending=False
                )
                .head(20)
            )


            st.bar_chart(
                extension_series
            )


        # ====================================================
        # TOP 10
        # ====================================================

        st.subheader(
            "🏋️ Objets les plus volumineux"
        )


        top_objects = (
            rustfs_summary.get(
                "top_objects",
                []
            )
        )


        if top_objects:

            top_df = pd.DataFrame(
                top_objects
            )


            top_df[
                "Taille"
            ] = (
                top_df[
                    "Taille_octets"
                ]
                .apply(
                    human_size
                )
            )


            st.dataframe(
                top_df[
                    [
                        "Fichier",
                        "Taille",
                        "Catégorie"
                    ]
                ],

                use_container_width=True,

                hide_index=True
            )


        # ====================================================
        # OBJETS RECENTS
        # ====================================================

        st.subheader(
            "📂 Objets récents"
        )


        recent_df = load_csv(
            str(
                RUSTFS_RECENT_FILE
            )
        )


        if recent_df.empty:

            st.info(
                "Aucun objet récent."
            )

        else:

            if (
                "Taille_octets"
                in recent_df.columns
            ):

                recent_df[
                    "Taille"
                ] = (
                    recent_df[
                        "Taille_octets"
                    ]
                    .apply(
                        human_size
                    )
                )


            max_rows = st.select_slider(
                "Nombre à afficher",
                options=[
                    25,
                    50,
                    100,
                    250,
                    500
                ],
                value=100
            )


            st.dataframe(
                recent_df[
                    [
                        "Fichier",
                        "Taille",
                        "Extension",
                        "Catégorie",
                        "Dernière modification"
                    ]
                ]
                .head(
                    max_rows
                ),

                use_container_width=True,

                hide_index=True
            )


# ============================================================
# ICEBERG
# ============================================================

elif page == "🧊 Iceberg":

    st.header(
        "🧊 Apache Iceberg"
    )


    iceberg_df = load_csv(
        str(
            ICEBERG_ROWS_FILE
        )
    )

    snapshots_df = load_csv(
        str(
            SNAPSHOTS_FILE
        )
    )

    stats_df = load_csv(
        str(
            SPARK_STATS_FILE
        )
    )

    activity_df = load_csv(
        str(
            SPARK_ACTIVITY_FILE
        )
    )


    if spark_running:

        st.warning(
            "⚡ Spark met actuellement "
            "Iceberg à jour."
        )


    if iceberg_df.empty:

        st.info(
            "Aucune donnée Iceberg mise en cache."
        )

        st.write(
            "Clique sur **⚡ Actualiser Spark / Iceberg**."
        )


    else:

        c1, c2, c3 = (
            st.columns(3)
        )


        c1.metric(
            "Lignes",
            spark_status.get(
                "total_rows",
                "-"
            )
        )


        c2.metric(
            "Snapshots",
            len(
                snapshots_df
            )
        )


        c3.metric(
            "Colonnes",
            len(
                iceberg_df.columns
            )
        )


        if not stats_df.empty:

            st.subheader(
                "Répartition des événements"
            )


            st.bar_chart(
                stats_df.set_index(
                    "type"
                )[
                    "nombre"
                ]
            )


        if (
            not activity_df.empty
            and "periode"
            in activity_df.columns
        ):

            st.subheader(
                "Activité Iceberg"
            )


            activity_df[
                "periode"
            ] = pd.to_datetime(
                activity_df[
                    "periode"
                ]
            )


            st.line_chart(
                activity_df
                .set_index(
                    "periode"
                )[
                    "nombre"
                ]
            )


        st.subheader(
            "📋 Données"
        )


        st.dataframe(
            iceberg_df.head(
                200
            ),

            use_container_width=True,

            hide_index=True
        )


        st.subheader(
            "📸 Snapshots"
        )


        if not snapshots_df.empty:

            st.dataframe(
                snapshots_df.tail(
                    100
                ),

                use_container_width=True,

                hide_index=True
            )


# ============================================================
# SPARK
# ============================================================

elif page == "⚡ Spark":

    st.header(
        "⚡ Apache Spark"
    )


    if spark_running:

        st.warning(
            "Traitement Spark en cours..."
        )


    status = (
        spark_status.get(
            "status"
        )
    )


    if status == "success":

        st.success(
            "Dernier traitement réussi."
        )


        c1, c2, c3 = (
            st.columns(3)
        )


        c1.metric(
            "Version",
            spark_status.get(
                "spark_version",
                "-"
            )
        )


        c2.metric(
            "Mode",
            spark_status.get(
                "master",
                "local[*]"
            )
        )


        c3.metric(
            "Lignes",
            spark_status.get(
                "total_rows",
                "-"
            )
        )


        stats_df = load_csv(
            str(
                SPARK_STATS_FILE
            )
        )


        if not stats_df.empty:

            st.subheader(
                "🔬 Spark SQL"
            )


            st.code(
                """
SELECT
    type,
    COUNT(*) AS nombre
FROM rustfs.opencode.logs
GROUP BY type
ORDER BY nombre DESC
"""
            )


            st.dataframe(
                stats_df,

                use_container_width=True,

                hide_index=True
            )


    elif status == "error":

        st.error(
            "Le dernier traitement Spark "
            "a échoué."
        )


        st.code(
            spark_status.get(
                "message",
                ""
            )
        )


    else:

        st.info(
            "Aucun traitement Spark."
        )


    log = read_log(
        SPARK_LOG_FILE
    )


    if log:

        with st.expander(
            "📜 Log Spark"
        ):

            st.code(
                log
            )


# ============================================================
# OPENCODE
# ============================================================

elif page == "🤖 OpenCode":

    st.header(
        "🤖 OpenCode"
    )


    logs_df = load_csv(
        str(
            RUSTFS_LOGS_FILE
        )
    )


    if logs_df.empty:

        st.info(
            "Aucun log OpenCode dans le cache."
        )


    else:

        c1, c2 = (
            st.columns(2)
        )


        c1.metric(
            "Logs",
            rustfs_summary.get(
                "logs_count",
                len(
                    logs_df
                )
            )
        )


        if (
            "Taille_octets"
            in logs_df.columns
        ):

            c2.metric(
                "Volume des 1000 derniers",
                human_size(
                    logs_df[
                        "Taille_octets"
                    ].sum()
                )
            )


        logs_df[
            "Dernière modification"
        ] = pd.to_datetime(
            logs_df[
                "Dernière modification"
            ]
        )


        graph = (
            logs_df.copy()
        )


        graph[
            "Jour"
        ] = (
            graph[
                "Dernière modification"
            ]
            .dt.date
        )


        graph = (
            graph
            .groupby(
                "Jour"
            )
            .size()
            .rename(
                "Logs"
            )
        )


        st.subheader(
            "Activité OpenCode"
        )


        st.bar_chart(
            graph
        )


        st.subheader(
            "📜 Derniers logs"
        )


        logs_df[
            "Taille"
        ] = (
            logs_df[
                "Taille_octets"
            ]
            .apply(
                human_size
            )
        )


        st.dataframe(
            logs_df[
                [
                    "Fichier",
                    "Taille",
                    "Dernière modification"
                ]
            ]
            .head(
                200
            ),

            use_container_width=True,

            hide_index=True
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()


st.caption(
    "Big Data Control Center • "
    f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
)
