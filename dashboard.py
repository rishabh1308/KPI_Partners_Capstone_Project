
import sqlite3
import math
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="MegaMart Analytics",
    layout="wide"
)


# ============================================================
# 2. DATABASE CONNECTION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "megamart.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def run_query(query, params=()):
    """
    Execute an SQL query and return the result as a DataFrame.
    Supports parameterized queries.
    """
    connection = get_connection()

    try:
        return pd.read_sql_query(
            query,
            connection,
            params=params
        )
    finally:
        connection.close()


# Check whether the database exists
if not DB_PATH.exists():
    st.error(f"Database not found: {DB_PATH}")
    st.stop()


# ============================================================
# 3. DASHBOARD HEADING
# ============================================================

st.title("MegaMart Analytics Dashboard")

st.write(
    "Sales, inventory and supplier performance overview."
)

st.divider()


# ============================================================
# 4. KPI SECTION
# ============================================================

sales_kpi = run_query("""
    SELECT
        COALESCE(SUM(total_amount), 0) AS total_revenue,
        COUNT(*) AS total_transactions
    FROM sales_transactions
""")

pending_kpi = run_query("""
    SELECT
        COUNT(*) AS pending_orders
    FROM purchase_orders
    WHERE delivery_date IS NULL
""")

stock_kpi = run_query("""
    SELECT
        COUNT(*) AS low_stock_cases
    FROM inventory
    WHERE quantity_on_hand <= 20
""")

total_revenue = sales_kpi.loc[0, "total_revenue"]
total_transactions = sales_kpi.loc[0, "total_transactions"]
pending_orders = pending_kpi.loc[0, "pending_orders"]
low_stock_cases = stock_kpi.loc[0, "low_stock_cases"]


st.subheader("Business Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Revenue",
    f"₹{total_revenue:,.0f}"
)

col2.metric(
    "Total Transactions",
    f"{total_transactions:,}"
)

col3.metric(
    "Pending Purchase Orders",
    f"{pending_orders:,}"
)

col4.metric(
    "Low Stock Cases",
    f"{low_stock_cases:,}"
)

st.divider()


# ============================================================
# 5. MONTHLY REVENUE TREND
# ============================================================

st.header("Sales Analytics")

st.subheader("Monthly Revenue Trend")

monthly_revenue = run_query("""
    SELECT
        strftime('%Y-%m', sale_date) AS month,
        SUM(total_amount) AS revenue
    FROM sales_transactions
    WHERE sale_date >= '2024-01-01'
      AND sale_date < '2025-01-01'
    GROUP BY strftime('%Y-%m', sale_date)
    ORDER BY month
""")

if not monthly_revenue.empty:

    fig_monthly = px.line(
        monthly_revenue,
        x="month",
        y="revenue",
        markers=True,
        title="Monthly Revenue in 2024",
        labels={
            "month": "Month",
            "revenue": "Revenue (₹)"
        }
    )

    fig_monthly.update_layout(
        xaxis_title="Month",
        yaxis_title="Revenue (₹)",
        hovermode="x unified"
    )

    st.plotly_chart(
        fig_monthly,
        use_container_width=True
    )

else:
    st.info("No monthly sales data available.")


# ============================================================
# 6. STORE-WISE REVENUE
# ============================================================

st.subheader("Store-wise Revenue")

store_revenue = run_query("""
    SELECT
        s.store_name,
        SUM(t.total_amount) AS revenue
    FROM sales_transactions t
    JOIN stores s
        ON t.store_id = s.store_id
    GROUP BY s.store_name
    ORDER BY revenue DESC
""")

if not store_revenue.empty:

    fig_store = px.bar(
        store_revenue,
        x="store_name",
        y="revenue",
        title="Revenue by Store",
        labels={
            "store_name": "Store",
            "revenue": "Revenue (₹)"
        },
        text_auto=".2s"
    )

    fig_store.update_layout(
        xaxis_title="Store",
        yaxis_title="Revenue (₹)"
    )

    st.plotly_chart(
        fig_store,
        use_container_width=True
    )


# ============================================================
# 7. CATEGORY-WISE REVENUE
# ============================================================

st.subheader("Category-wise Revenue")

category_revenue = run_query("""
    SELECT
        p.category,
        SUM(t.total_amount) AS revenue
    FROM sales_transactions t
    JOIN products p
        ON t.product_id = p.product_id
    GROUP BY p.category
    ORDER BY revenue DESC
""")

if not category_revenue.empty:

    fig_category = px.pie(
        category_revenue,
        names="category",
        values="revenue",
        title="Revenue Contribution by Category",
        hole=0.4
    )

    fig_category.update_traces(
        textposition="inside",
        textinfo="percent+label"
    )

    st.plotly_chart(
        fig_category,
        use_container_width=True
    )


# ============================================================
# 8. INVENTORY OVERVIEW
# ============================================================

st.divider()

st.header("Inventory Management")

inventory_summary = run_query("""
    SELECT
        s.store_name,
        COUNT(i.inventory_id) AS product_count,
        SUM(i.quantity_on_hand) AS total_stock
    FROM inventory i
    JOIN stores s
        ON i.store_id = s.store_id
    GROUP BY s.store_name
    ORDER BY total_stock DESC
""")

col1, col2 = st.columns(2)

with col1:

    fig_inventory = px.bar(
        inventory_summary,
        x="store_name",
        y="total_stock",
        title="Total Inventory by Store",
        labels={
            "store_name": "Store",
            "total_stock": "Units in Stock"
        },
        text_auto=True
    )

    st.plotly_chart(
        fig_inventory,
        use_container_width=True
    )


with col2:

    fig_products = px.bar(
        inventory_summary,
        x="store_name",
        y="product_count",
        title="Number of Products by Store",
        labels={
            "store_name": "Store",
            "product_count": "Number of Products"
        },
        text_auto=True
    )

    st.plotly_chart(
        fig_products,
        use_container_width=True
    )


# ============================================================
# 9. LOW STOCK ALERTS
# ============================================================

st.subheader("Low Stock Alerts")

low_stock = run_query("""
    SELECT
        s.store_name,
        p.product_name,
        i.quantity_on_hand
    FROM inventory i
    JOIN stores s
        ON i.store_id = s.store_id
    JOIN products p
        ON i.product_id = p.product_id
    WHERE i.quantity_on_hand <= 20
    ORDER BY i.quantity_on_hand ASC
""")

if not low_stock.empty:

    st.dataframe(
        low_stock,
        use_container_width=True,
        hide_index=True
    )

else:
    st.success("No products currently meet the low-stock threshold.")


# ============================================================
# 10. DEMAND-BASED REORDER RECOMMENDATIONS
# ============================================================

st.subheader("Demand-Based Reorder Recommendations")

reorder_data = run_query("""
    SELECT
        s.store_name,
        p.product_name,
        i.quantity_on_hand,

        COALESCE(
            SUM(t.quantity_sold),
            0
        ) AS annual_units_sold

    FROM inventory i

    JOIN stores s
        ON i.store_id = s.store_id

    JOIN products p
        ON i.product_id = p.product_id

    LEFT JOIN sales_transactions t
        ON i.store_id = t.store_id
        AND i.product_id = t.product_id
        AND t.sale_date >= '2024-01-01'
        AND t.sale_date < '2025-01-01'

    GROUP BY
        i.inventory_id,
        s.store_name,
        p.product_name,
        i.quantity_on_hand
""")

# Calculate average daily demand
reorder_data["average_daily_demand"] = (
    reorder_data["annual_units_sold"] / 366
)


# Calculate remaining stock coverage in days
def calculate_days_remaining(row):

    if row["average_daily_demand"] > 0:

        return (
            row["quantity_on_hand"]
            / row["average_daily_demand"]
        )

    return None


reorder_data["days_remaining"] = reorder_data.apply(
    calculate_days_remaining,
    axis=1
)


# Calculate suggested reorder quantity
def calculate_reorder_quantity(row):

    target_stock = (
        row["average_daily_demand"] * 30
    )

    quantity_needed = (
        target_stock - row["quantity_on_hand"]
    )

    return max(0, math.ceil(quantity_needed))


reorder_data["suggested_reorder"] = reorder_data.apply(
    calculate_reorder_quantity,
    axis=1
)


# Identify products requiring replenishment
def determine_stock_status(row):

    if (
        row["average_daily_demand"] > 0
        and row["days_remaining"] < 14
    ):
        return "REORDER REQUIRED"

    return "SUFFICIENT STOCK"


reorder_data["status"] = reorder_data.apply(
    determine_stock_status,
    axis=1
)


# Filter products requiring replenishment
reorder_required = reorder_data[
    reorder_data["status"] == "REORDER REQUIRED"
].copy()


if not reorder_required.empty:

    reorder_required["average_daily_demand"] = (
        reorder_required["average_daily_demand"].round(3)
    )

    reorder_required["days_remaining"] = (
        reorder_required["days_remaining"].round(1)
    )

    st.dataframe(
        reorder_required[
            [
                "store_name",
                "product_name",
                "quantity_on_hand",
                "annual_units_sold",
                "average_daily_demand",
                "days_remaining",
                "suggested_reorder",
                "status"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

else:

    st.success(
        "No products currently require replenishment."
    )


# ============================================================
# 11. SUPPLIER PERFORMANCE
# ============================================================

st.divider()

st.header("Supplier Performance")

supplier_data = run_query("""
    SELECT
        s.supplier_name,

        COUNT(po.po_id) AS total_orders,

        SUM(
            CASE
                WHEN po.delivery_date IS NOT NULL
                THEN 1
                ELSE 0
            END
        ) AS delivered_orders,

        SUM(
            CASE
                WHEN po.delivery_date IS NULL
                THEN 1
                ELSE 0
            END
        ) AS pending_orders,

        ROUND(
            AVG(
                CASE
                    WHEN po.delivery_date IS NOT NULL
                    THEN julianday(po.delivery_date)
                         - julianday(po.order_date)
                END
            ),
            2
        ) AS avg_delivery_days

    FROM purchase_orders po

    JOIN suppliers s
        ON po.supplier_id = s.supplier_id

    GROUP BY
        s.supplier_id,
        s.supplier_name

    ORDER BY delivered_orders DESC
""")

if not supplier_data.empty:

    supplier_data["completion_rate"] = (
        supplier_data["delivered_orders"]
        / supplier_data["total_orders"] * 100
    ).round(2)


    st.subheader("Supplier Summary")

    st.dataframe(
        supplier_data,
        use_container_width=True,
        hide_index=True
    )


    # Supplier delivery completion chart
    fig_supplier = px.bar(
        supplier_data,
        x="supplier_name",
        y="completion_rate",
        title="Supplier Delivery Completion Rate",
        labels={
            "supplier_name": "Supplier",
            "completion_rate": "Completion Rate (%)"
        },
        text="completion_rate"
    )

    fig_supplier.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="outside"
    )

    fig_supplier.update_layout(
        yaxis_title="Completion Rate (%)",
        yaxis_range=[0, 110]
    )

    st.plotly_chart(
        fig_supplier,
        use_container_width=True
    )


    # Average supplier delivery time
    fig_delivery = px.bar(
        supplier_data,
        x="supplier_name",
        y="avg_delivery_days",
        title="Average Supplier Delivery Time",
        labels={
            "supplier_name": "Supplier",
            "avg_delivery_days": "Average Delivery Days"
        },
        text_auto=True
    )

    st.plotly_chart(
        fig_delivery,
        use_container_width=True
    )

else:

    st.info("No supplier data available.")


# ============================================================
# 12. DOWNLOAD REPORTS
# ============================================================

st.divider()

st.header("Download Reports")


def convert_to_csv(dataframe):

    return dataframe.to_csv(
        index=False
    ).encode("utf-8")


col1, col2, col3 = st.columns(3)


with col1:

    st.download_button(
        label="Download Monthly Revenue",
        data=convert_to_csv(monthly_revenue),
        file_name="monthly_revenue.csv",
        mime="text/csv"
    )


with col2:

    st.download_button(
        label="Download Inventory Report",
        data=convert_to_csv(reorder_data),
        file_name="inventory_reorder_report.csv",
        mime="text/csv"
    )


with col3:

    st.download_button(
        label="Download Supplier Report",
        data=convert_to_csv(supplier_data),
        file_name="supplier_performance.csv",
        mime="text/csv"
    )


# ============================================================
# 13. INTERACTIVE STORE ANALYSIS
# ============================================================

st.divider()

st.header("Explore Individual Stores")

store_options = run_query("""
    SELECT
        store_id,
        store_name
    FROM stores
    ORDER BY store_name
""")


if not store_options.empty:

    selected_store = st.selectbox(
        "Select a Store",
        store_options["store_name"].tolist()
    )


    # Store-level revenue and sales metrics
    selected_store_data = run_query("""
        SELECT
            s.store_name,

            COUNT(t.transaction_id) AS transactions,

            COALESCE(
                SUM(t.quantity_sold),
                0
            ) AS units_sold,

            COALESCE(
                SUM(t.total_amount),
                0
            ) AS revenue

        FROM stores s

        LEFT JOIN sales_transactions t
            ON s.store_id = t.store_id

        WHERE s.store_name = ?

        GROUP BY s.store_name
    """, (selected_store,))


    if not selected_store_data.empty:

        row = selected_store_data.iloc[0]

        metric1, metric2, metric3 = st.columns(3)

        metric1.metric(
            "Revenue",
            f"₹{row['revenue']:,.0f}"
        )

        metric2.metric(
            "Transactions",
            f"{row['transactions']:,}"
        )

        metric3.metric(
            "Units Sold",
            f"{row['units_sold']:,}"
        )


        # Product-wise revenue for selected store
        product_data = run_query("""
            SELECT
                p.product_name,
                SUM(t.total_amount) AS revenue

            FROM sales_transactions t

            JOIN products p
                ON t.product_id = p.product_id

            JOIN stores s
                ON t.store_id = s.store_id

            WHERE s.store_name = ?

            GROUP BY p.product_name

            ORDER BY revenue DESC
        """, (selected_store,))


        if not product_data.empty:

            fig_selected = px.bar(
                product_data,
                x="product_name",
                y="revenue",
                title=f"Product Revenue - {selected_store}",
                labels={
                    "product_name": "Product",
                    "revenue": "Revenue (₹)"
                },
                text_auto=".2s"
            )

            st.plotly_chart(
                fig_selected,
                use_container_width=True
            )

        else:

            st.info("No product sales found for this store.")

else:

    st.warning("No stores found in the database.")


# ============================================================
# 14. FOOTER
# ============================================================

st.divider()

st.caption(
    "MegaMart Analytics | Sales, Inventory and Supplier Management"
)

st.success("Dashboard loaded successfully.")
