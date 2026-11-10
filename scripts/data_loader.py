
import csv
import sqlite3
from pathlib import Path


# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
DB_PATH = BASE_DIR / "megamart.db"


def read_csv(filename):
    """Read a processed CSV file and return its records."""
    file_path = PROCESSED_DIR / filename

    with open(file_path, "r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def load_table(connection, table_name, records, columns, converters=None):
    """Insert records into a database table."""

    if not records:
        print(f"{table_name}: 0 records inserted")
        return

    converters = converters or {}

    placeholders = ", ".join(["?"] * len(columns))
    column_names = ", ".join(columns)

    query = (
        f"INSERT INTO {table_name} ({column_names}) "
        f"VALUES ({placeholders})"
    )

    values = []

    for record in records:
        row = []

        for column in columns:
            value = record[column]

            if value == "":
                value = None

            if value is not None and column in converters:
                value = converters[column](value)

            row.append(value)

        values.append(tuple(row))

    connection.executemany(query, values)

    print(f"{table_name}: {len(values)} records inserted")


def main():
    print("MEGAMART DATA LOADING PIPELINE")
    print("-" * 40)

    connection = sqlite3.connect(DB_PATH)

    try:
        # Enable foreign-key checking for this connection
        connection.execute("PRAGMA foreign_keys = ON")

        # Verify foreign keys are enabled
        fk_status = connection.execute(
            "PRAGMA foreign_keys"
        ).fetchone()[0]

        if fk_status != 1:
            raise RuntimeError("Foreign keys could not be enabled")

        # Read validated CSV files
        stores = read_csv("stores.csv")
        suppliers = read_csv("suppliers.csv")
        products = read_csv("products.csv")
        sales = read_csv("sales_transactions.csv")
        inventory = read_csv("inventory.csv")
        purchase_orders = read_csv("purchase_orders.csv")

        # All deletes and inserts happen in one transaction.
        # If an insertion fails, the changes are rolled back.
        with connection:

            # Clear old data in child-to-parent order
            connection.execute("DELETE FROM purchase_orders")
            connection.execute("DELETE FROM inventory")
            connection.execute("DELETE FROM sales_transactions")
            connection.execute("DELETE FROM products")
            connection.execute("DELETE FROM suppliers")
            connection.execute("DELETE FROM stores")

            print("\nLoading records...\n")

            # 1. Parent tables
            load_table(
                connection,
                "stores",
                stores,
                ["store_id", "store_name", "location", "manager_name"],
                {"store_id": int}
            )

            load_table(
                connection,
                "suppliers",
                suppliers,
                ["supplier_id", "supplier_name", "contact_person", "phone"],
                {"supplier_id": int}
            )

            # 2. Products depend on suppliers
            load_table(
                connection,
                "products",
                products,
                [
                    "product_id", "product_name", "category",
                    "unit_price", "supplier_id"
                ],
                {"product_id": int, "unit_price": float, "supplier_id": int}
            )

            # 3. Sales and inventory depend on stores and products
            load_table(
                connection,
                "sales_transactions",
                sales,
                [
                    "transaction_id", "store_id", "product_id",
                    "quantity_sold", "unit_price", "total_amount", "sale_date"
                ],
                {
                    "transaction_id": int,
                    "store_id": int,
                    "product_id": int,
                    "quantity_sold": int,
                    "unit_price": float,
                    "total_amount": float
                }
            )

            load_table(
                connection,
                "inventory",
                inventory,
                [
                    "inventory_id", "store_id",
                    "product_id", "quantity_on_hand"
                ],
                {
                    "inventory_id": int,
                    "store_id": int,
                    "product_id": int,
                    "quantity_on_hand": int
                }
            )

            # 4. Purchase orders depend on suppliers
            load_table(
                connection,
                "purchase_orders",
                purchase_orders,
                ["po_id", "supplier_id", "order_date", "delivery_date"],
                {"po_id": int, "supplier_id": int}
            )

        print("\nData loading completed successfully!")

    except Exception as error:
        print("\nERROR: Data loading failed.")
        print("Reason:", error)
        print("Database changes have been rolled back.")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
