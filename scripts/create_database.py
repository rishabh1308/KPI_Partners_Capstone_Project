
import sqlite3
from pathlib import Path

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Database and schema paths
DB_PATH = BASE_DIR / "megamart.db"
SCHEMA_PATH = BASE_DIR / "database" / "create_schema.sql"

# Connect to SQLite
conn = sqlite3.connect(DB_PATH)

try:
    # Enable foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON")

    # Read schema
    with open(SCHEMA_PATH, "r") as file:
        schema = file.read()

    # Execute SQL
    conn.executescript(schema)

    print("Database created successfully!")

    # Verify tables
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name;
    """)

    print("\nTables created:")

    for table in cursor.fetchall():
        print(table[0])

finally:
    conn.close()
