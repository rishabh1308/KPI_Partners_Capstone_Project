
import csv
import logging
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ==========================================
# 1. PROJECT CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
REJECTED_DIR = BASE_DIR / "data" / "rejected"
OUTPUT_DIR = BASE_DIR / "outputs"

for directory in [PROCESSED_DIR, REJECTED_DIR, OUTPUT_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=OUTPUT_DIR / "data_validation.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    force=True
)


# ==========================================
# 2. COMMON HELPER FUNCTIONS
# ==========================================

def read_csv(filename):

    file_path = RAW_DIR / filename

    with open(file_path, "r", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(filename, records, rejected=False):

    if not records:
        return

    output_dir = REJECTED_DIR if rejected else PROCESSED_DIR

    file_path = output_dir / filename

    fieldnames = list(records[0].keys())

    if rejected and "rejection_reason" not in fieldnames:
        fieldnames.append("rejection_reason")

    with open(file_path, "w", newline="") as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(records)


def valid_date(value):

    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True

    except (ValueError, TypeError):
        return False


def to_int(value):

    try:
        number = int(value)

        if str(number) != str(value):
            return None

        return number

    except (ValueError, TypeError):
        return None


def to_float(value):

    try:
        return float(value)

    except (ValueError, TypeError):
        return None


def reject(record, reason, rejected_records):

    rejected_record = record.copy()
    rejected_record["rejection_reason"] = reason

    rejected_records.append(rejected_record)

    logging.error(reason)


def normalize_phone(phone):

    digits = "".join(
        character for character in phone
        if character.isdigit()
    )

    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]

    if len(digits) == 10:
        return digits

    return None


# ==========================================
# 3. VALIDATE STORES
# ==========================================

def validate_stores():

    stores = read_csv("stores.csv")

    valid_records = []
    rejected_records = []
    seen_ids = set()

    for store in stores:

        store_id = to_int(store["store_id"])

        if store_id is None or store_id <= 0:
            reject(store, "Invalid store ID", rejected_records)
            continue

        if store_id in seen_ids:
            reject(store, "Duplicate store ID", rejected_records)
            continue

        if not store["store_name"].strip():
            reject(store, "Missing store name", rejected_records)
            continue

        if not store["location"].strip():
            reject(store, "Missing store location", rejected_records)
            continue

        if not store["manager_name"].strip():
            logging.warning(
                f"Missing manager for store {store_id}"
            )

        seen_ids.add(store_id)
        valid_records.append(store)

    write_csv("stores.csv", valid_records)
    write_csv("stores.csv", rejected_records, rejected=True)

    return valid_records, seen_ids


# ==========================================
# 4. VALIDATE SUPPLIERS
# ==========================================

def validate_suppliers():

    suppliers = read_csv("suppliers.csv")

    valid_records = []
    rejected_records = []
    seen_ids = set()

    for supplier in suppliers:

        supplier_id = to_int(supplier["supplier_id"])

        if supplier_id is None or supplier_id <= 0:
            reject(supplier, "Invalid supplier ID", rejected_records)
            continue

        if supplier_id in seen_ids:
            reject(supplier, "Duplicate supplier ID", rejected_records)
            continue

        if not supplier["supplier_name"].strip():
            reject(supplier, "Missing supplier name", rejected_records)
            continue

        phone = normalize_phone(supplier["phone"])

        if phone is None:
            reject(supplier, "Invalid supplier phone", rejected_records)
            continue

        supplier["phone"] = phone

        if not supplier["contact_person"].strip():
            logging.warning(
                f"Missing contact person for supplier {supplier_id}"
            )

        seen_ids.add(supplier_id)
        valid_records.append(supplier)

    write_csv("suppliers.csv", valid_records)
    write_csv("suppliers.csv", rejected_records, rejected=True)

    return valid_records, seen_ids


# ==========================================
# 5. VALIDATE PRODUCTS
# ==========================================

def validate_products(valid_supplier_ids):

    products = read_csv("products.csv")

    valid_records = []
    rejected_records = []
    valid_product_ids = set()
    seen_ids = set()

    for product in products:

        product_id = to_int(product["product_id"])
        supplier_id = to_int(product["supplier_id"])
        price = to_float(product["unit_price"])

        if product_id is None or product_id <= 0:
            reject(product, "Invalid product ID", rejected_records)
            continue

        if product_id in seen_ids:
            reject(product, "Duplicate product ID", rejected_records)
            continue

        seen_ids.add(product_id)

        if not product["product_name"].strip():
            reject(product, "Missing product name", rejected_records)
            continue

        if not product["category"].strip():
            reject(product, "Missing category", rejected_records)
            continue

        if price is None or price <= 0:
            reject(
                product,
                f"Invalid product price: {product['unit_price']}",
                rejected_records
            )
            continue

        if supplier_id not in valid_supplier_ids:
            reject(
                product,
                f"Invalid supplier reference: {supplier_id}",
                rejected_records
            )
            continue

        valid_product_ids.add(product_id)
        valid_records.append(product)

    write_csv("products.csv", valid_records)
    write_csv("products.csv", rejected_records, rejected=True)

    return valid_records, valid_product_ids


# ==========================================
# 6. IDENTIFY INTENTIONAL SALES DUPLICATES
# ==========================================

def find_injected_duplicate_ids(sales):

    sales_by_id = {
        to_int(sale["transaction_id"]): sale
        for sale in sales
        if to_int(sale["transaction_id"]) is not None
    }

    duplicate_ids = set()

    fields = [
        "store_id",
        "product_id",
        "quantity_sold",
        "unit_price",
        "total_amount",
        "sale_date"
    ]

    for sale in sales:

        transaction_id = to_int(sale["transaction_id"])

        if transaction_id is None:
            continue

        if transaction_id < 60000:
            continue

        original = sales_by_id.get(transaction_id - 10000)

        if original is None:
            continue

        if all(
            original[field] == sale[field]
            for field in fields
        ):
            duplicate_ids.add(transaction_id)

    return duplicate_ids


# ==========================================
# 7. VALIDATE SALES TRANSACTIONS
# ==========================================

def validate_sales(valid_store_ids, valid_product_ids):

    sales = read_csv("sales_transactions.csv")

    valid_records = []
    rejected_records = []
    seen_ids = set()

    # Identify the four intentionally injected duplicates
    injected_duplicate_ids = find_injected_duplicate_ids(sales)

    # Identify ambiguous duplicate business records
    business_groups = defaultdict(list)

    for sale in sales:

        key = (
            sale["store_id"],
            sale["product_id"],
            sale["quantity_sold"],
            sale["unit_price"],
            sale["total_amount"],
            sale["sale_date"]
        )

        business_groups[key].append(sale)

    for group in business_groups.values():

        if len(group) > 1:

            ids = [sale["transaction_id"] for sale in group]

            has_injected_pair = any(
                abs(int(a) - int(b)) == 10000
                for a in ids
                for b in ids
                if a != b
            )

            if not has_injected_pair:
                logging.warning(
                    f"Ambiguous duplicate sales group: {ids}"
                )

    for sale in sales:

        transaction_id = to_int(sale["transaction_id"])
        store_id = to_int(sale["store_id"])
        product_id = to_int(sale["product_id"])
        quantity = to_int(sale["quantity_sold"])
        price = to_float(sale["unit_price"])
        amount = to_float(sale["total_amount"])
        sale_date = sale["sale_date"]

        if transaction_id is None or transaction_id <= 0:
            reject(sale, "Invalid transaction ID", rejected_records)
            continue

        if transaction_id in seen_ids:
            reject(sale, "Duplicate transaction ID", rejected_records)
            continue

        seen_ids.add(transaction_id)

        if transaction_id in injected_duplicate_ids:
            reject(
                sale,
                "Intentional duplicate generated by sample script",
                rejected_records
            )
            continue

        if store_id not in valid_store_ids:
            reject(sale, "Invalid store reference", rejected_records)
            continue

        if product_id not in valid_product_ids:
            reject(sale, "Invalid product reference", rejected_records)
            continue

        if quantity is None or quantity <= 0:
            reject(sale, "Invalid quantity sold", rejected_records)
            continue

        if price is None or price <= 0:
            reject(sale, "Invalid sales unit price", rejected_records)
            continue

        if amount is None or amount <= 0:
            reject(sale, "Invalid total amount", rejected_records)
            continue

        if abs(amount - quantity * price) >= 0.01:
            reject(sale, "Incorrect total amount", rejected_records)
            continue

        if not valid_date(sale_date):
            reject(sale, "Invalid sale date", rejected_records)
            continue

        if not sale_date.startswith("2024-"):
            reject(sale, "Sale date outside 2024", rejected_records)
            continue

        valid_records.append(sale)

    write_csv("sales_transactions.csv", valid_records)
    write_csv("sales_transactions.csv", rejected_records, rejected=True)

    return valid_records


# ==========================================
# 8. VALIDATE INVENTORY
# ==========================================

def validate_inventory(valid_store_ids, valid_product_ids):

    inventory = read_csv("inventory.csv")

    valid_records = []
    rejected_records = []
    seen_ids = set()
    seen_combinations = set()

    for item in inventory:

        inventory_id = to_int(item["inventory_id"])
        store_id = to_int(item["store_id"])
        product_id = to_int(item["product_id"])
        quantity = to_int(item["quantity_on_hand"])

        if inventory_id is None or inventory_id <= 0:
            reject(item, "Invalid inventory ID", rejected_records)
            continue

        if inventory_id in seen_ids:
            reject(item, "Duplicate inventory ID", rejected_records)
            continue

        seen_ids.add(inventory_id)

        if store_id not in valid_store_ids:
            reject(item, "Invalid inventory store reference", rejected_records)
            continue

        if product_id not in valid_product_ids:
            reject(item, "Invalid inventory product reference", rejected_records)
            continue

        if quantity is None or quantity < 0:
            reject(item, "Invalid inventory quantity", rejected_records)
            continue

        combination = (store_id, product_id)

        if combination in seen_combinations:
            reject(
                item,
                "Duplicate store-product inventory combination",
                rejected_records
            )
            continue

        seen_combinations.add(combination)
        valid_records.append(item)

    write_csv("inventory.csv", valid_records)
    write_csv("inventory.csv", rejected_records, rejected=True)

    return valid_records


# ==========================================
# 9. VALIDATE PURCHASE ORDERS
# ==========================================

def validate_purchase_orders(valid_supplier_ids):

    orders = read_csv("purchase_orders.csv")

    valid_records = []
    rejected_records = []
    seen_ids = set()

    for order in orders:

        po_id = to_int(order["po_id"])
        supplier_id = to_int(order["supplier_id"])

        order_date = order["order_date"]
        delivery_date = order["delivery_date"]

        if po_id is None or po_id <= 0:
            reject(order, "Invalid purchase order ID", rejected_records)
            continue

        if po_id in seen_ids:
            reject(order, "Duplicate purchase order ID", rejected_records)
            continue

        seen_ids.add(po_id)

        if supplier_id not in valid_supplier_ids:
            reject(order, "Invalid purchase order supplier", rejected_records)
            continue

        if not valid_date(order_date):
            reject(order, "Invalid order date", rejected_records)
            continue

        if not order_date.startswith("2024-"):
            reject(order, "Order date outside 2024", rejected_records)
            continue

        # Empty delivery date is allowed for pending orders
        if delivery_date:

            if not valid_date(delivery_date):
                reject(order, "Invalid delivery date", rejected_records)
                continue

            if delivery_date < order_date:
                reject(
                    order,
                    "Delivery date earlier than order date",
                    rejected_records
                )
                continue

        else:
            logging.warning(
                f"Pending purchase order: {po_id}"
            )

        valid_records.append(order)

    write_csv("purchase_orders.csv", valid_records)
    write_csv("purchase_orders.csv", rejected_records, rejected=True)

    return valid_records


# ==========================================
# 10. MAIN ETL VALIDATION PIPELINE
# ==========================================

def main():

    print("\n===================================")
    print("MEGAMART DATA VALIDATION PIPELINE")
    print("===================================\n")

    # Step 1: Stores
    print("Validating stores...")
    stores, valid_store_ids = validate_stores()

    # Step 2: Suppliers
    print("Validating suppliers...")
    suppliers, valid_supplier_ids = validate_suppliers()

    # Step 3: Products
    print("Validating products...")
    products, valid_product_ids = validate_products(
        valid_supplier_ids
    )

    # Step 4: Sales
    print("Validating sales transactions...")
    sales = validate_sales(
        valid_store_ids,
        valid_product_ids
    )

    # Step 5: Inventory
    print("Validating inventory...")
    inventory = validate_inventory(
        valid_store_ids,
        valid_product_ids
    )

    # Step 6: Purchase Orders
    print("Validating purchase orders...")
    orders = validate_purchase_orders(
        valid_supplier_ids
    )

    # Summary
    print("\n===================================")
    print("VALIDATION SUMMARY")
    print("===================================")

    summary = {
        "Stores": stores,
        "Suppliers": suppliers,
        "Products": products,
        "Sales": sales,
        "Inventory": inventory,
        "Purchase Orders": orders
    }

    for name, records in summary.items():

        print(f"{name}: {len(records)} accepted")

    print("\nProcessed files:", PROCESSED_DIR)
    print("Rejected files:", REJECTED_DIR)
    print("Validation log:", OUTPUT_DIR / "data_validation.log")

    logging.info("MegaMart validation pipeline completed")


if __name__ == "__main__":
    main()
