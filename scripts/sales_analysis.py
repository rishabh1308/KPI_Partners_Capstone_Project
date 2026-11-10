
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "megamart.db"

connection = sqlite3.connect(DB_PATH)

query = """
SELECT
    p.product_id,
    p.product_name,
    p.category,
    SUM(s.quantity_sold) AS total_quantity_sold,
    ROUND(SUM(s.total_amount), 2) AS total_revenue
FROM sales_transactions AS s
JOIN products AS p
    ON s.product_id = p.product_id
GROUP BY
    p.product_id,
    p.product_name,
    p.category
ORDER BY total_revenue DESC;
"""

store_query = """
    SELECT
        st.store_id,
        st.store_name,
        st.location,
        COUNT(s.transaction_id) AS total_transactions,
        SUM(s.quantity_sold) AS total_quantity_sold,
        ROUND(SUM(s.total_amount), 2) AS total_revenue
    FROM sales_transactions AS s
    JOIN stores AS st
        ON s.store_id = st.store_id
    GROUP BY
        st.store_id,
        st.store_name,
        st.location
    ORDER BY total_revenue DESC;
    """

# Monthly revenue analysis
monthly_query = """
SELECT
    strftime('%Y-%m', sale_date) AS sales_month,
    COUNT(transaction_id) AS total_transactions,
    SUM(quantity_sold) AS total_quantity_sold,
    ROUND(SUM(total_amount), 2) AS monthly_revenue
FROM sales_transactions
WHERE strftime('%Y', sale_date) = '2024'
GROUP BY strftime('%Y-%m', sale_date)
ORDER BY sales_month ASC;
"""

# Category-wise sales analysis
category_query = """
SELECT
    p.category,
    COUNT(s.transaction_id) AS total_transactions,
    SUM(s.quantity_sold) AS total_quantity_sold,
    ROUND(SUM(s.total_amount), 2) AS total_revenue
FROM sales_transactions AS s
JOIN products AS p
    ON s.product_id = p.product_id
GROUP BY p.category
ORDER BY total_revenue DESC;
"""

# Top 5 products by quantity sold
top_products_query = """
SELECT
    p.product_id,
    p.product_name,
    p.category,
    SUM(s.quantity_sold) AS total_quantity_sold,
    ROUND(SUM(s.total_amount), 2) AS total_revenue
FROM sales_transactions AS s
JOIN products AS p
    ON s.product_id = p.product_id
GROUP BY
    p.product_id,
    p.product_name,
    p.category
ORDER BY total_quantity_sold DESC
LIMIT 5;
"""

try:
    cursor = connection.cursor()
    cursor.execute(query)

    results = cursor.fetchall()

    print("\nTOP PRODUCTS BY REVENUE")
    print("-" * 75)
    print(
        f"{'Product ID':<12}"
        f"{'Product Name':<25}"
        f"{'Quantity':<12}"
        f"{'Revenue':>15}"
    )
    print("-" * 75)

    for row in results:
        product_id, product_name, category, quantity, revenue = row

        print(
            f"{product_id:<12}"
            f"{product_name:<25}"
            f"{quantity:<12}"
            f"{revenue:>15,.2f}"
        )

    cursor.execute(store_query)
    store_results = cursor.fetchall()

    print("\n\nSTORE-WISE REVENUE ANALYSIS")
    print("-" * 85)

    for row in store_results:
        store_id, name, location, transactions, quantity, revenue = row

        print(f"\nStore: {name}")
        print(f"Location: {location}")
        print(f"Total transactions: {transactions}")
        print(f"Total quantity sold: {quantity}")
        print(f"Total revenue: ₹{revenue:,.2f}")

    cursor.execute(monthly_query)
    monthly_results = cursor.fetchall()

    print("\n\nMONTHLY REVENUE ANALYSIS")
    print("-" * 75)

    for row in monthly_results:
        month, transactions, quantity, revenue = row

        print(f"\nMonth: {month}")
        print(f"Total transactions: {transactions}")
        print(f"Total quantity sold: {quantity}")
        print(f"Monthly revenue: ₹{revenue:,.2f}")

    # Find highest-revenue month
    if monthly_results:
        best_month = max(monthly_results, key=lambda row: row[3])

        print("\nHIGHEST REVENUE MONTH")
        print(f"Month: {best_month[0]}")
        print(f"Revenue: ₹{best_month[3]:,.2f}")

    cursor.execute(category_query)
    category_results = cursor.fetchall()

    print("\n\nCATEGORY-WISE SALES ANALYSIS")
    print("-" * 75)

    for row in category_results:
        category, transactions, quantity, revenue = row

        print(f"\nCategory: {category}")
        print(f"Total transactions: {transactions}")
        print(f"Total quantity sold: {quantity}")
        print(f"Total revenue: ₹{revenue:,.2f}")

    cursor.execute(top_products_query)
    top_products = cursor.fetchall()

    print("\n\nTOP 5 PRODUCTS BY QUANTITY SOLD")
    print("-" * 75)

    for row in top_products:
        product_id, name, category, quantity, revenue = row

        print(f"\nProduct: {name}")
        print(f"Category: {category}")
        print(f"Quantity sold: {quantity}")
        print(f"Total revenue: ₹{revenue:,.2f}")


finally:
    connection.close()
