
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "megamart.db"

print("Database path:", DB_PATH)

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")

cursor = conn.cursor()

print("Foreign keys enabled:",
      cursor.execute("PRAGMA foreign_keys").fetchone()[0])

# Test foreign key constraint
try:
    cursor.execute("""
        INSERT INTO products
        (product_id, product_name, category, unit_price, supplier_id)
        VALUES (9999, 'Test Product', 'Test', 100, 999)
    """)

    conn.rollback()
    print("FAILED: Invalid supplier was accepted")

except sqlite3.IntegrityError as e:
    conn.rollback()
    print("PASSED:", e)

# Test CHECK constraint
try:
    cursor.execute("""
        INSERT INTO products
        (product_id, product_name, category, unit_price, supplier_id)
        VALUES (9998, 'Invalid Product', 'Test', -100, 1)
    """)

    conn.rollback()
    print("FAILED: Negative price was accepted")

except sqlite3.IntegrityError as e:
    conn.rollback()
    print("PASSED:", e)

conn.close()
