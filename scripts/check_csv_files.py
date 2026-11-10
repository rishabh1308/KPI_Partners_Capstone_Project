import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "raw"

for file_path in sorted(DATA_DIR.glob("*.csv")):

    with open(file_path, "r", newline="") as file:
        reader = csv.reader(file)

        header = next(reader, None)
        records = sum(1 for row in reader)

    print(f"\nFile: {file_path.name}")
    print(f"Columns: {header}")
    print(f"Records: {records}")