
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "megamart.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()



query = """
SELECT
    st.store_name,
    st.location,
    COUNT(i.product_id) AS total_products,
    SUM(i.quantity_on_hand) AS total_stock
FROM inventory AS i
JOIN stores AS st
    ON i.store_id = st.store_id
GROUP BY
    st.store_id,
    st.store_name,
    st.location
ORDER BY total_stock DESC;
"""

# Low-stock product analysis
low_stock_query = """
SELECT
    st.store_name,
    p.product_name,
    p.category,
    i.quantity_on_hand
FROM inventory AS i
JOIN stores AS st
    ON i.store_id = st.store_id
JOIN products AS p
    ON i.product_id = p.product_id
WHERE i.quantity_on_hand <= 20
ORDER BY i.quantity_on_hand ASC;
"""


# Inventory valuation by store
valuation_query = """
SELECT
    st.store_name,
    SUM(i.quantity_on_hand) AS total_units,
    ROUND(
        SUM(i.quantity_on_hand * p.unit_price), 2
    ) AS inventory_value
FROM inventory AS i
JOIN stores AS st
    ON i.store_id = st.store_id
JOIN products AS p
    ON i.product_id = p.product_id
GROUP BY
    st.store_id,
    st.store_name
ORDER BY inventory_value DESC;
"""


# Inventory replenishment report
replenishment_query = """
SELECT
    st.store_name,
    p.product_name,
    i.quantity_on_hand,
    CASE
        WHEN i.quantity_on_hand = 0 THEN 'OUT OF STOCK'
        WHEN i.quantity_on_hand <= 5 THEN 'CRITICAL'
        WHEN i.quantity_on_hand <= 20 THEN 'LOW STOCK'
        ELSE 'NORMAL'
    END AS stock_status
FROM inventory AS i
JOIN stores AS st
    ON i.store_id = st.store_id
JOIN products AS p
    ON i.product_id = p.product_id
WHERE i.quantity_on_hand <= 20
ORDER BY i.quantity_on_hand ASC;
"""

cursor.execute(query)
results = cursor.fetchall()

print("\nSTORE-WISE INVENTORY SUMMARY")
print("-" * 65)

for row in results:
    store, location, products, stock = row

    print(f"\nStore: {store}")
    print(f"Location: {location}")
    print(f"Products stocked: {products}")
    print(f"Total stock: {stock}")

cursor.execute(low_stock_query)
low_stock_results = cursor.fetchall()

print("\n\nLOW-STOCK PRODUCTS")
print("-" * 75)

if low_stock_results:
    for row in low_stock_results:
        store, product, category, quantity = row

        print(f"\nStore: {store}")
        print(f"Product: {product}")
        print(f"Category: {category}")
        print(f"Available stock: {quantity}")
else:
    print("No low-stock products found.")

cursor.execute(valuation_query)
valuation_results = cursor.fetchall()

print("\n\nINVENTORY VALUATION BY STORE")
print("-" * 65)

for row in valuation_results:
    store, units, value = row

    print(f"\nStore: {store}")
    print(f"Total units: {units}")
    print(f"Estimated inventory value: ₹{value:,.2f}")

cursor.execute(replenishment_query)
replenishment_results = cursor.fetchall()

print("\n\nINVENTORY REPLENISHMENT REPORT")
print("-" * 75)

for row in replenishment_results:
    store, product, quantity, status = row

    print(f"\nStore: {store}")
    print(f"Product: {product}")
    print(f"Available quantity: {quantity}")
    print(f"Status: {status}")

connection.close()

