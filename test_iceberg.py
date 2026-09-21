from pyiceberg.catalog import load_catalog
from datetime import datetime
import pyarrow as pa

catalog = load_catalog("rustfs")
table = catalog.load_table("opencode.logs")

data = pa.table({
    "timestamp": [datetime.now()],
    "session_id": ["test-session"],
    "type": ["test"],
    "content": ["Hello Iceberg depuis OpenCode"],
    "source_file": ["manual-test"]
}, schema=table.schema().as_arrow())

table.append(data)

print("Donnée ajoutée dans Iceberg")
