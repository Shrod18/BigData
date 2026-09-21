from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("Spark-Iceberg-RustFS")
    .master("local[*]")

    # --------------------------------------------------
    # Dépendances
    # --------------------------------------------------

    .config(
        "spark.jars.packages",
        ",".join([
            "org.apache.iceberg:iceberg-spark-runtime-4.1_2.13:1.11.0",
            "org.apache.hadoop:hadoop-aws:3.4.2",
        ])
    )

    # --------------------------------------------------
    # Iceberg
    # --------------------------------------------------

    .config(
        "spark.sql.extensions",
        "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions"
    )

    .config(
        "spark.sql.catalog.rustfs",
        "org.apache.iceberg.spark.SparkCatalog"
    )

    .config(
        "spark.sql.catalog.rustfs.type",
        "hadoop"
    )

    # IMPORTANT :
    # on passe de s3:// à s3a://
    .config(
        "spark.sql.catalog.rustfs.warehouse",
        "s3a://opencode-data/spark-warehouse"
    )

    # --------------------------------------------------
    # S3A -> RustFS
    # --------------------------------------------------

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
        "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider"
    )

    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")


print("\n==============================")
print(" SPARK + ICEBERG + RUSTFS")
print("==============================\n")


# --------------------------------------------------
# Namespace Iceberg
# --------------------------------------------------

print("1. Création namespace")

spark.sql("""
CREATE NAMESPACE IF NOT EXISTS rustfs.opencode
""")


# --------------------------------------------------
# Table Iceberg
# --------------------------------------------------

print("2. Création table Iceberg")

spark.sql("""
CREATE TABLE IF NOT EXISTS rustfs.opencode.logs (
    timestamp TIMESTAMP,
    session_id STRING,
    type STRING,
    content STRING,
    source_file STRING
)
USING iceberg
""")


# --------------------------------------------------
# Insertion
# --------------------------------------------------

print("3. Insertion d'une donnée")

spark.sql("""
INSERT INTO rustfs.opencode.logs
VALUES (
    current_timestamp(),
    'spark-test',
    'test',
    'Hello depuis Apache Spark + Apache Iceberg + RustFS',
    'spark_iceberg.py'
)
""")


# --------------------------------------------------
# Lecture
# --------------------------------------------------

print("\n4. Contenu de la table\n")

spark.sql("""
SELECT *
FROM rustfs.opencode.logs
""").show(
    truncate=False
)


# --------------------------------------------------
# Snapshots Iceberg
# --------------------------------------------------

print("\n5. Snapshots Iceberg\n")

spark.sql("""
SELECT
    committed_at,
    snapshot_id,
    operation
FROM rustfs.opencode.logs.snapshots
ORDER BY committed_at DESC
""").show(
    truncate=False
)


print("\n==============================")
print(" Spark fonctionne correctement")
print("==============================")

print("\nSpark UI : http://localhost:4040")

input("\nAppuie sur Entrée pour arrêter Spark...")

spark.stop()
