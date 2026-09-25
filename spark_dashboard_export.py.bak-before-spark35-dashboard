import json
import traceback
from datetime import datetime
from pathlib import Path

from pyspark.sql import SparkSession


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_DIR = Path.home() / "BigData"
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

CACHE_DIR.mkdir(
    parents=True,
    exist_ok=True
)

STATUS_FILE = CACHE_DIR / "spark_status.json"

ICEBERG_ROWS_FILE = CACHE_DIR / "iceberg_rows.csv"
SNAPSHOTS_FILE = CACHE_DIR / "snapshots.csv"
STATS_FILE = CACHE_DIR / "spark_stats.csv"
ACTIVITY_FILE = CACHE_DIR / "spark_activity.csv"

ICEBERG_TABLE = "rustfs.opencode.logs"


# ============================================================
# STATUS
# ============================================================

def write_status(status, **kwargs):

    data = {
        "status": status,
        "updated_at": datetime.now().isoformat(
            timespec="seconds"
        ),
        **kwargs
    }

    temporary = STATUS_FILE.with_suffix(
        ".tmp"
    )

    temporary.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    temporary.replace(
        STATUS_FILE
    )


# ============================================================
# DEBUT
# ============================================================

write_status(
    "running",
    message="Démarrage du traitement Spark"
)

spark = None


try:

    # ========================================================
    # SPARK LOCAL
    # ========================================================

    spark = (
        SparkSession.builder

        .appName(
            "BigData-Spark-Dashboard-Export"
        )

        .master(
            "local[*]"
        )

        # ----------------------------------------------------
        # WSL
        # ----------------------------------------------------

        .config(
            "spark.driver.host",
            "127.0.0.1"
        )

        .config(
            "spark.driver.bindAddress",
            "127.0.0.1"
        )

        # Pas besoin d'interface Spark UI pour ce job court
        .config(
            "spark.ui.enabled",
            "false"
        )

        .config(
            "spark.sql.shuffle.partitions",
            "4"
        )

        # ----------------------------------------------------
        # ICEBERG + S3A
        # ----------------------------------------------------

        .config(
            "spark.jars.packages",
            ",".join([
                "org.apache.iceberg:"
                "iceberg-spark-runtime-4.1_2.13:1.11.0",

                "org.apache.hadoop:"
                "hadoop-aws:3.4.2"
            ])
        )

        .config(
            "spark.sql.extensions",
            "org.apache.iceberg.spark.extensions."
            "IcebergSparkSessionExtensions"
        )

        # ----------------------------------------------------
        # CATALOGUE ICEBERG
        # ----------------------------------------------------

        .config(
            "spark.sql.catalog.rustfs",
            "org.apache.iceberg.spark.SparkCatalog"
        )

        .config(
            "spark.sql.catalog.rustfs.type",
            "hadoop"
        )

        .config(
            "spark.sql.catalog.rustfs.warehouse",
            "s3a://opencode-data/spark-warehouse"
        )

        # ----------------------------------------------------
        # RUSTFS / S3A
        # ----------------------------------------------------

        .config(
            "spark.hadoop.fs.s3a.impl",
            "org.apache.hadoop.fs.s3a.S3AFileSystem"
        )

        .config(
            "spark.hadoop.fs.s3a.endpoint",
            "http://127.0.0.1:9000"
        )

        .config(
            "spark.hadoop.fs.s3a.endpoint.region",
            "us-east-1"
        )

        .config(
            "spark.hadoop.fs.s3a.path.style.access",
            "true"
        )

        .config(
            "spark.hadoop.fs.s3a.connection.ssl.enabled",
            "false"
        )

        .config(
            "spark.hadoop.fs.s3a.access.key",
            "rustfsadmin"
        )

        .config(
            "spark.hadoop.fs.s3a.secret.key",
            "rustfsadmin"
        )

        .config(
            "spark.hadoop.fs.s3a.aws.credentials.provider",
            "org.apache.hadoop.fs.s3a."
            "SimpleAWSCredentialsProvider"
        )

        .getOrCreate()
    )


    spark.sparkContext.setLogLevel(
        "WARN"
    )


    # ========================================================
    # NOMBRE TOTAL DE LIGNES
    # ========================================================

    total_rows = (
        spark.sql(
            f"""
            SELECT COUNT(*) AS nombre
            FROM {ICEBERG_TABLE}
            """
        )
        .first()["nombre"]
    )


    # ========================================================
    # APERCU DES DONNEES
    #
    # Limité à 2000 lignes pour ne pas charger inutilement
    # le dashboard.
    # ========================================================

    iceberg_rows = (
        spark.sql(
            f"""
            SELECT *
            FROM {ICEBERG_TABLE}
            ORDER BY timestamp DESC
            LIMIT 2000
            """
        )
        .toPandas()
    )

    iceberg_rows.to_csv(
        ICEBERG_ROWS_FILE,
        index=False
    )


    # ========================================================
    # SNAPSHOTS
    # ========================================================

    snapshots = (
        spark.sql(
            f"""
            SELECT
                committed_at,
                snapshot_id,
                operation
            FROM {ICEBERG_TABLE}.snapshots
            ORDER BY committed_at
            """
        )
        .toPandas()
    )

    snapshots.to_csv(
        SNAPSHOTS_FILE,
        index=False
    )


    # ========================================================
    # STATS PAR TYPE
    # ========================================================

    stats = (
        spark.sql(
            f"""
            SELECT
                type,
                COUNT(*) AS nombre
            FROM {ICEBERG_TABLE}
            GROUP BY type
            ORDER BY nombre DESC
            """
        )
        .toPandas()
    )

    stats.to_csv(
        STATS_FILE,
        index=False
    )


    # ========================================================
    # ACTIVITE DANS LE TEMPS
    # ========================================================

    activity = (
        spark.sql(
            f"""
            SELECT
                date_trunc(
                    'hour',
                    timestamp
                ) AS periode,

                COUNT(*) AS nombre

            FROM {ICEBERG_TABLE}

            GROUP BY
                date_trunc(
                    'hour',
                    timestamp
                )

            ORDER BY periode
            """
        )
        .toPandas()
    )

    activity.to_csv(
        ACTIVITY_FILE,
        index=False
    )


    # ========================================================
    # SUCCES
    # ========================================================

    write_status(
        "success",

        message=(
            "Traitement Spark terminé correctement"
        ),

        spark_version=spark.version,

        master=spark.sparkContext.master,

        total_rows=int(
            total_rows
        ),

        snapshots=len(
            snapshots
        ),

        displayed_rows=len(
            iceberg_rows
        )
    )


    print(
        "Export Spark / Iceberg terminé."
    )


except Exception as e:

    error = traceback.format_exc()

    write_status(
        "error",

        message=str(e),

        error=error[-8000:]
    )

    print(error)

    raise


finally:

    if spark is not None:

        try:

            spark.stop()

        except Exception:
            pass
