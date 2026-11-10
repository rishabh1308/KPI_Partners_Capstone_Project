
-- ==========================================
-- MegaMart Supermarket Database
-- Problem 1: Schema Design
-- Database: SQLite
-- ==========================================

PRAGMA foreign_keys = ON;

-- 1. STORES TABLE
CREATE TABLE IF NOT EXISTS stores (
    store_id INTEGER PRIMARY KEY,
    store_name VARCHAR(100) NOT NULL,
    location VARCHAR(100) NOT NULL,
    manager_name VARCHAR(100)
);

-- 2. SUPPLIERS TABLE
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id INTEGER PRIMARY KEY,
    supplier_name VARCHAR(150) NOT NULL,
    contact_person VARCHAR(100),
    phone VARCHAR(20)
);

-- 3. PRODUCTS TABLE
CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY,
    product_name VARCHAR(150) NOT NULL,
    category VARCHAR(100) NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL
        CHECK (unit_price > 0),
    supplier_id INTEGER NOT NULL,

    FOREIGN KEY (supplier_id)
        REFERENCES suppliers(supplier_id)
);

-- 4. SALES TRANSACTIONS TABLE
CREATE TABLE IF NOT EXISTS sales_transactions (
    transaction_id INTEGER PRIMARY KEY,
    store_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity_sold INTEGER NOT NULL
        CHECK (quantity_sold > 0),
    unit_price DECIMAL(10,2) NOT NULL
        CHECK (unit_price > 0),
    total_amount DECIMAL(12,2) NOT NULL
        CHECK (total_amount > 0),
    sale_date DATE NOT NULL
        CHECK (
            length(sale_date) = 10
            AND date(sale_date) IS NOT NULL
        ),

    FOREIGN KEY (store_id)
        REFERENCES stores(store_id),

    FOREIGN KEY (product_id)
        REFERENCES products(product_id),

    CHECK (
        ABS(total_amount - quantity_sold * unit_price) < 0.01
    )
);

-- 5. INVENTORY TABLE
CREATE TABLE IF NOT EXISTS inventory (
    inventory_id INTEGER PRIMARY KEY,
    store_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity_on_hand INTEGER NOT NULL
        CHECK (quantity_on_hand >= 0),

    FOREIGN KEY (store_id)
        REFERENCES stores(store_id),

    FOREIGN KEY (product_id)
        REFERENCES products(product_id),

    UNIQUE (store_id, product_id)
);

-- 6. PURCHASE ORDERS TABLE
CREATE TABLE IF NOT EXISTS purchase_orders (
    po_id INTEGER PRIMARY KEY,
    supplier_id INTEGER NOT NULL,
    order_date DATE NOT NULL,
    delivery_date DATE,

    FOREIGN KEY (supplier_id)
        REFERENCES suppliers(supplier_id),

    CHECK (
        length(order_date) = 10
        AND date(order_date) IS NOT NULL
    ),

    CHECK (
        delivery_date IS NULL
        OR (
            length(delivery_date) = 10
            AND date(delivery_date) IS NOT NULL
            AND delivery_date >= order_date
        )
    )
);

-- ==========================================
-- INDEXES FOR QUERY PERFORMANCE
-- ==========================================

CREATE INDEX IF NOT EXISTS idx_sales_store
ON sales_transactions(store_id);

CREATE INDEX IF NOT EXISTS idx_sales_product
ON sales_transactions(product_id);

CREATE INDEX IF NOT EXISTS idx_sales_date
ON sales_transactions(sale_date);

CREATE INDEX IF NOT EXISTS idx_inventory_product
ON inventory(product_id);

CREATE INDEX IF NOT EXISTS idx_purchase_supplier
ON purchase_orders(supplier_id);

-- ==========================================
-- SCHEMA CREATION COMPLETE
-- ==========================================
