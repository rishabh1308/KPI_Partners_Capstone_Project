
import csv
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent.parent
REJECTED_DIR = BASE_DIR / "data" / "rejected"

files = [
    "sales_transactions.csv",
    "inventory.csv",
    "products.csv",
    "purchase_orders.csv"
]

for filename in files:

    file_path = REJECTED_DIR / filename

    print(f"\n===== {filename} =====")

    if not file_path.exists():
        print("No rejected file found.")
        continue

    with open(file_path, "r", newline="") as file:

        reader = csv.DictReader(file)
        records = list(reader)

    reasons = Counter(
        record["rejection_reason"]
        for record in records
    )

    print("Total rejected:", len(records))

    for reason, count in reasons.items():
        print(f"{reason}: {count}")
