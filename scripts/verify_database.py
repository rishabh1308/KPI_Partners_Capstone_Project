
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "megamart.db"


def main():
    connection = sqlite3.connect(DB_PATH)

    try:
        print("MEGAMART DATABASE VERIFICATION")
        print("-" * 40)

        # 1. Verify record counts
        tables = [
            "stores",
            "suppliers",
            "products",
            "sales_transactions",
            "inventory",
            "purchase_orders"
        ]

        print("\n1. RECORD COUNTS")

        for table in tables:
            count = connection.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

            print(f"{table}: {count}")

        # 2. Check foreign-key integrity
        print("\n2. FOREIGN KEY CHECK")

        fk_errors = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        if fk_errors:
            print("FAILED: Foreign-key violations found.")
            for error in fk_errors:
                print(error)
        else:
            print("PASSED: No foreign-key violations.")

        # 3. Check sales amount calculations
        print("\n3. SALES AMOUNT CHECK")

        incorrect_sales = connection.execute("""
            SELECT COUNT(*)
            FROM sales_transactions
            WHERE ABS(total_amount - quantity_sold * unit_price) > 0.01
        """).fetchone()[0]

        if incorrect_sales == 0:
            print("PASSED: All sales amounts are correct.")
        else:
            print(f"FAILED: {incorrect_sales} incorrect sales records.")

        # 4. Check inventory uniqueness
        print("\n4. INVENTORY UNIQUENESS CHECK")

        duplicate_inventory = connection.execute("""
            SELECT store_id, product_id, COUNT(*)
            FROM inventory
            GROUP BY store_id, product_id
            HAVING COUNT(*) > 1
        """).fetchall()

        if not duplicate_inventory:
            print("PASSED: No duplicate store-product combinations.")
        else:
            print("FAILED: Duplicate inventory combinations found.")
            print(duplicate_inventory)

        # 5. Check pending purchase orders
        print("\n5. PENDING PURCHASE ORDERS")

        pending = connection.execute("""
            SELECT COUNT(*)
            FROM purchase_orders
            WHERE delivery_date IS NULL
        """).fetchone()[0]

        print(f"Pending purchase orders: {pending}")

        # 6. Sales summary
        print("\n6. SALES SUMMARY")

        total_sales = connection.execute("""
            SELECT ROUND(SUM(total_amount), 2)
            FROM sales_transactions
        """).fetchone()[0]

        print(f"Total sales revenue: {total_sales}")

        print("\nVerification completed.")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
