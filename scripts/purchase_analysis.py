import math
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "megamart.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()



# Supplier-wise purchase order analysis
supplier_query = """
SELECT
    s.supplier_id,
    s.supplier_name,
    COUNT(po.po_id) AS total_orders,

    SUM(
        CASE
            WHEN po.delivery_date IS NOT NULL THEN 1
            ELSE 0
        END
    ) AS delivered_orders,

    SUM(
        CASE
            WHEN po.delivery_date IS NULL THEN 1
            ELSE 0
        END
    ) AS pending_orders

FROM suppliers AS s
LEFT JOIN purchase_orders AS po
    ON s.supplier_id = po.supplier_id

GROUP BY
    s.supplier_id,
    s.supplier_name

ORDER BY total_orders DESC;
"""


# Average supplier delivery time
delivery_query = """
SELECT
    s.supplier_name,
    COUNT(po.delivery_date) AS delivered_orders,
    ROUND(
        AVG(
            julianday(po.delivery_date) -
            julianday(po.order_date)
        ), 2
    ) AS avg_delivery_days,
    MIN(
        julianday(po.delivery_date) -
        julianday(po.order_date)
    ) AS fastest_delivery_days,
    MAX(
        julianday(po.delivery_date) -
        julianday(po.order_date)
    ) AS slowest_delivery_days

FROM suppliers AS s
LEFT JOIN purchase_orders AS po
    ON s.supplier_id = po.supplier_id

GROUP BY
    s.supplier_id,
    s.supplier_name

ORDER BY avg_delivery_days ASC;
"""

# Supplier delivery completion rate
completion_query = """
SELECT
    s.supplier_name,
    COUNT(po.po_id) AS total_orders,

    SUM(
        CASE
            WHEN po.delivery_date IS NOT NULL THEN 1
            ELSE 0
        END
    ) AS delivered_orders,

    ROUND(
        100.0 * SUM(
            CASE
                WHEN po.delivery_date IS NOT NULL THEN 1
                ELSE 0
            END
        ) / COUNT(po.po_id),
        2
    ) AS delivery_rate

FROM suppliers AS s
LEFT JOIN purchase_orders AS po
    ON s.supplier_id = po.supplier_id

GROUP BY
    s.supplier_id,
    s.supplier_name

ORDER BY delivery_rate DESC;
"""


# Inventory optimization using historical demand

optimization_query = """
SELECT
    st.store_name,
    p.product_name,
    i.quantity_on_hand,

    COALESCE(SUM(s.quantity_sold), 0) AS annual_units_sold,

    ROUND(
        COALESCE(SUM(s.quantity_sold), 0) / 366.0,
        3
    ) AS average_daily_demand

FROM inventory AS i

JOIN stores AS st
    ON i.store_id = st.store_id

JOIN products AS p
    ON i.product_id = p.product_id

LEFT JOIN sales_transactions AS s
    ON s.store_id = i.store_id
    AND s.product_id = i.product_id
    AND s.sale_date >= '2024-01-01'
    AND s.sale_date < '2025-01-01'

GROUP BY
    i.inventory_id,
    st.store_name,
    p.product_name,
    i.quantity_on_hand

ORDER BY average_daily_demand DESC;
"""


cursor.execute(supplier_query)
results = cursor.fetchall()

print("\nSUPPLIER-WISE PURCHASE ORDER ANALYSIS")
print("-" * 75)

for row in results:
    supplier_id, name, total, delivered, pending = row

    print(f"\nSupplier: {name}")
    print(f"Total orders: {total}")
    print(f"Delivered orders: {delivered}")
    print(f"Pending orders: {pending}")

cursor.execute(delivery_query)
delivery_results = cursor.fetchall()

print("\n\nSUPPLIER DELIVERY TIME ANALYSIS")
print("-" * 75)

for row in delivery_results:
    supplier, delivered, average, fastest, slowest = row

    print(f"\nSupplier: {supplier}")
    print(f"Delivered orders: {delivered}")
    print(f"Average delivery time: {average:.2f} days")
    print(f"Fastest delivery: {fastest:.0f} days")
    print(f"Slowest delivery: {slowest:.0f} days")

cursor.execute(completion_query)
completion_results = cursor.fetchall()

print("\n\nSUPPLIER DELIVERY COMPLETION RATE")
print("-" * 75)

for row in completion_results:
    supplier, total, delivered, rate = row

    print(f"\nSupplier: {supplier}")
    print(f"Total orders: {total}")
    print(f"Delivered orders: {delivered}")
    print(f"Delivery completion rate: {rate}%")

cursor.execute(optimization_query)
optimization_results = cursor.fetchall()

print("\n\nINVENTORY OPTIMIZATION REPORT")
print("-" * 80)

for row in optimization_results:

    store, product, stock, annual_sales, daily_demand = row

    if daily_demand > 0:
        days_remaining = stock / daily_demand

        reorder_quantity = max(
            0,
            math.ceil((daily_demand * 30) - stock)
        )

        if days_remaining <= 14:
            status = "REORDER REQUIRED"
        else:
            status = "SUFFICIENT STOCK"

        print(f"\nStore: {store}")
        print(f"Product: {product}")
        print(f"Current stock: {stock}")
        print(f"Annual units sold: {annual_sales}")
        print(f"Average daily demand: {daily_demand}")
        print(f"Estimated days remaining: {days_remaining:.1f}")
        print(f"Suggested reorder quantity: {reorder_quantity}")
        print(f"Status: {status}")

    else:
        print(f"\nStore: {store}")
        print(f"Product: {product}")
        print(f"Current stock: {stock}")
        print("No recorded sales during 2024.")
        print("Status: REVIEW DEMAND")



connection.close()
