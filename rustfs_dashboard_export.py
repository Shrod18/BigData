import csv
import json
import os
import traceback

from collections import Counter
from datetime import datetime
from pathlib import Path

import boto3


# ============================================================
# CONFIGURATION
# ============================================================

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


STATUS_FILE = (
    CACHE_DIR
    / "rustfs_status.json"
)

SUMMARY_FILE = (
    CACHE_DIR
    / "rustfs_summary.json"
)

RECENT_FILE = (
    CACHE_DIR
    / "rustfs_recent.csv"
)

LOGS_FILE = (
    CACHE_DIR
    / "rustfs_logs.csv"
)


RUSTFS_ENDPOINT = os.getenv(
    "RUSTFS_ENDPOINT",
    "http://127.0.0.1:9000"
)

RUSTFS_ACCESS_KEY = os.getenv(
    "RUSTFS_ACCESS_KEY",
    "rustfsadmin"
)

RUSTFS_SECRET_KEY = os.getenv(
    "RUSTFS_SECRET_KEY",
    "rustfsadmin"
)

BUCKET = "opencode-data"


# ============================================================
# OUTILS
# ============================================================

def extension_from_key(key):

    filename = key.rsplit(
        "/",
        1
    )[-1]

    if "." not in filename:
        return "Sans extension"

    return filename.rsplit(
        ".",
        1
    )[-1].lower()


def category_from_key(key):

    if key.startswith(
        "spark-warehouse/"
    ):
        return "Iceberg / Spark"

    if key.startswith(
        "logs/"
    ):
        return "Logs OpenCode"

    return "Projet / fichiers"


def atomic_json(
    path,
    data
):

    temporary = path.with_suffix(
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
        path
    )


def atomic_csv(
    path,
    rows
):

    temporary = path.with_suffix(
        ".tmp"
    )

    fieldnames = [
        "Fichier",
        "Taille_octets",
        "Dernière modification",
        "Extension",
        "Catégorie"
    ]


    with temporary.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(
            rows
        )


    temporary.replace(
        path
    )


def write_status(
    status,
    message,
    **kwargs
):

    atomic_json(
        STATUS_FILE,
        {
            "status":
                status,

            "message":
                message,

            "updated_at":
                datetime.now().isoformat(
                    timespec="seconds"
                ),

            **kwargs
        }
    )


# ============================================================
# DEBUT
# ============================================================

write_status(
    "running",
    "Inventaire RustFS en cours..."
)


try:

    s3 = boto3.client(
        "s3",
        endpoint_url=RUSTFS_ENDPOINT,
        aws_access_key_id=RUSTFS_ACCESS_KEY,
        aws_secret_access_key=RUSTFS_SECRET_KEY,
        region_name="us-east-1"
    )


    paginator = s3.get_paginator(
        "list_objects_v2"
    )


    rows = []

    total_size = 0

    categories = Counter()

    extensions = Counter()

    extension_sizes = Counter()

    daily_activity = Counter()


    # ========================================================
    # PARCOURS DU BUCKET
    # ========================================================

    for page in paginator.paginate(
        Bucket=BUCKET,
        PaginationConfig={
            "PageSize": 1000
        }
    ):

        for obj in page.get(
            "Contents",
            []
        ):

            key = obj[
                "Key"
            ]


            # Ancien PyIceberg :
            # on l'ignore complètement.
            if key.startswith(
                "iceberg/"
            ):
                continue


            size = int(
                obj[
                    "Size"
                ]
            )

            modified = obj[
                "LastModified"
            ]

            extension = (
                extension_from_key(
                    key
                )
            )

            category = (
                category_from_key(
                    key
                )
            )


            row = {
                "Fichier":
                    key,

                "Taille_octets":
                    size,

                "Dernière modification":
                    modified.isoformat(),

                "Extension":
                    extension,

                "Catégorie":
                    category
            }


            rows.append(
                row
            )


            total_size += size

            categories[
                category
            ] += 1

            extensions[
                extension
            ] += 1

            extension_sizes[
                extension
            ] += size

            daily_activity[
                modified.date().isoformat()
            ] += 1


    # ========================================================
    # TRIS
    # ========================================================

    rows_recent = sorted(
        rows,
        key=lambda x:
            x[
                "Dernière modification"
            ],
        reverse=True
    )


    biggest = sorted(
        rows,
        key=lambda x:
            x[
                "Taille_octets"
            ],
        reverse=True
    )


    logs = [
        row
        for row in rows_recent
        if row[
            "Catégorie"
        ] == "Logs OpenCode"
    ]


    # On n'enregistre que les éléments utiles au dashboard.
    #
    # Le dashboard n'a donc jamais besoin de charger
    # 100 000 objets.
    recent_for_dashboard = (
        rows_recent[
            :1000
        ]
    )

    logs_for_dashboard = (
        logs[
            :1000
        ]
    )


    # ========================================================
    # RESUME
    # ========================================================

    summary = {

        "generated_at":
            datetime.now().isoformat(
                timespec="seconds"
            ),

        "total_objects":
            len(
                rows
            ),

        "total_size":
            total_size,

        "logs_count":
            categories.get(
                "Logs OpenCode",
                0
            ),

        "iceberg_objects":
            categories.get(
                "Iceberg / Spark",
                0
            ),

        "category_counts":
            dict(
                categories
            ),

        "extension_counts":
            dict(
                extensions
            ),

        "extension_sizes":
            dict(
                extension_sizes
            ),

        "daily_activity":
            dict(
                sorted(
                    daily_activity.items()
                )
            ),

        "top_objects":
            biggest[
                :10
            ]
    }


    # ========================================================
    # ECRITURE DU CACHE
    # ========================================================

    atomic_json(
        SUMMARY_FILE,
        summary
    )

    atomic_csv(
        RECENT_FILE,
        recent_for_dashboard
    )

    atomic_csv(
        LOGS_FILE,
        logs_for_dashboard
    )


    write_status(
        "success",
        "Inventaire RustFS terminé.",
        total_objects=len(
            rows
        ),
        total_size=total_size
    )


    print(
        f"Inventaire RustFS terminé : "
        f"{len(rows)} objets."
    )


except Exception as e:

    error = traceback.format_exc()

    write_status(
        "error",
        str(e),
        error=error[
            -8000:
        ]
    )

    print(
        error
    )

    raise
