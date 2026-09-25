#!/usr/bin/env python3
"""
Pipeline streaming du projet BigData :

Redpanda
   ↓
Spark Structured Streaming
   ↓
Transformation JSON
   ↓
Apache Iceberg
   ↓
RustFS / S3

Table cible :
    rustfs.opencode.logs_stream
"""

from __future__ import annotations

import os
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, to_timestamp
from pyspark.sql.types import StructField, StructType, StringType

BROKER = os.getenv("REDPANDA_BROKER", "localhost:19092")
TOPIC = os.getenv("REDPANDA_TOPIC", "opencode.logs")

RUSTFS_ENDPOINT = os.getenv(
    "RUSTFS_ENDPOINT",
    "http://127.0.0.1:9000",
)
RUSTFS_ACCESS_KEY = os.getenv(
    "RUSTFS_ACCESS_KEY",
    "rustfsadmin",
)
RUSTFS_SECRET_KEY = os.getenv(
    "RUSTFS_SECRET_KEY",
    "rustfsadmin",
)

WAREHOUSE = os.getenv(
    "ICEBERG_WAREHOUSE",
    "s3a://opencode-data/spark-warehouse",
)
TABLE = os.getenv(
    "ICEBERG_STREAM_TABLE",
    "rustfs.opencode.logs_stream",
)

STATE_DIR = Path.home() / ".local" / "state" / "bigdata"
CHECKPOINT = STATE_DIR / "spark-redpanda-checkpoint"
CHECKPOINT.mkdir(parents=True, exist_ok=True)

# Versions cohérentes avec ton installation Spark/Iceberg actuelle.
PACKAGES = ",".join(
    [
        "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.11.0",
        "org.apache.hadoop:hadoop-aws:3.3.4",
        "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.9",
    ]
)

print("[SPARK] 1/5 Démarrage de Spark...", flush=True)

spark = (
    SparkSession.builder
    .appName("BigData-Redpanda-Iceberg-Streaming")
    .master("local[1]")
    .config("spark.driver.host", "127.0.0.1")
    .config("spark.driver.bindAddress", "127.0.0.1")
    .config("spark.jars.packages", PACKAGES)
    .config(
        "spark.sql.extensions",
        "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
    )
    .config(
        "spark.sql.catalog.rustfs",
        "org.apache.iceberg.spark.SparkCatalog",
    )
    .config("spark.sql.catalog.rustfs.type", "hadoop")
    .config("spark.sql.catalog.rustfs.warehouse", WAREHOUSE)
    .config("spark.hadoop.fs.s3a.endpoint", RUSTFS_ENDPOINT)
    .config("spark.hadoop.fs.s3a.access.key", RUSTFS_ACCESS_KEY)
    .config("spark.hadoop.fs.s3a.secret.key", RUSTFS_SECRET_KEY)
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
    .config(
        "spark.hadoop.fs.s3a.aws.credentials.provider",
        "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider",
    )
    .config("spark.sql.shuffle.partitions", "4")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")
print("[SPARK] 2/5 SparkSession créée.", flush=True)

print("[SPARK] 3/5 Connexion à Iceberg / RustFS...", flush=True)
spark.sql("CREATE NAMESPACE IF NOT EXISTS rustfs.opencode")
print("[SPARK] Namespace Iceberg OK.", flush=True)

spark.sql(
    f"""
    CREATE TABLE IF NOT EXISTS {TABLE} (
        timestamp TIMESTAMP,
        session_id STRING,
        type STRING,
        content STRING,
        source_file STRING
    )
    USING iceberg
    """
)

print("[SPARK] 4/5 Table Iceberg prête.", flush=True)

schema = StructType(
    [
        StructField("timestamp", StringType(), True),
        StructField("session_id", StringType(), True),
        StructField("type", StringType(), True),
        StructField("content", StringType(), True),
        StructField("source_file", StringType(), True),
    ]
)

print("[SPARK] 5/5 Connexion à Redpanda...", flush=True)

raw = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", BROKER)
    .option("subscribe", TOPIC)
    .option("startingOffsets", "latest")
    .option("failOnDataLoss", "false")
    .load()
)

parsed = (
    raw.selectExpr("CAST(value AS STRING) AS json_value")
    .select(from_json(col("json_value"), schema).alias("data"))
    .select("data.*")
    .withColumn("timestamp", to_timestamp(col("timestamp")))
    .filter(col("content").isNotNull())
)


def write_to_iceberg(batch_df, batch_id: int) -> None:
    batch_df.persist()
    try:
        rows = batch_df.count()
        if rows == 0:
            return

        (
            batch_df.select(
                "timestamp",
                "session_id",
                "type",
                "content",
                "source_file",
            )
            .writeTo(TABLE)
            .append()
        )

        print(
            f"[SPARK] Batch {batch_id}: "
            f"{rows} ligne(s) écrite(s) dans {TABLE}."
        )
    finally:
        batch_df.unpersist()


print(f"[SPARK] Redpanda   : {BROKER}")
print(f"[SPARK] Topic      : {TOPIC}")
print(f"[SPARK] Iceberg    : {TABLE}")
print(f"[SPARK] Checkpoint : {CHECKPOINT}")

query = (
    parsed.writeStream
    .foreachBatch(write_to_iceberg)
    .option("checkpointLocation", str(CHECKPOINT))
    .trigger(processingTime="5 seconds")
    .start()
)

query.awaitTermination()
