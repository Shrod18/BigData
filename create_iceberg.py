from pyiceberg.catalog import load_catalog
import pyarrow as pa

catalog = load_catalog("rustfs")

catalog.create_namespace_if_not_exists("opencode")

schema = pa.schema([
    ("timestamp", pa.timestamp("us")),
    ("session_id", pa.string()),
    ("type", pa.string()),
    ("content", pa.string()),
    ("source_file", pa.string()),
])

table = catalog.create_table_if_not_exists(
    "opencode.logs",
    schema=schema
)

print("Table Iceberg prête :", table.name())
print("Location :", table.location())
