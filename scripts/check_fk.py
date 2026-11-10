
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "megamart.db"

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")

cursor = conn.cursor()

# Check enforcement
cursor.execute("PRAGMA foreign_keys")
print("Foreign key enforcement:", cursor.fetchone()[0])

# Check actual foreign key definition
cursor.execute("PRAGMA foreign_key_list(products)")
print("Products foreign keys:", cursor.fetchall())

# Check whether supplier 999 exists
cursor.execute("""
    SELECT *
    FROM suppliers
    WHERE supplier_id = 999
""")

print("Supplier 999:", cursor.fetchone())

conn.close()
