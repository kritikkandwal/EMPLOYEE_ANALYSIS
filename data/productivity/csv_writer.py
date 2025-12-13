import csv
import os

CSV_PATH = "data/productivity/productivity.csv"

# Ensure directory exists
os.makedirs("data/productivity", exist_ok=True)


def update_csv_for_day(date, completed, total):
    score = round((completed / total) * 100) if total > 0 else 0

    row = {
        "date": date,
        "completed": completed,
        "total": total,
        "score": score
    }

    # If file does not exist → create with header
    file_exists = os.path.isfile(CSV_PATH)

    with open(CSV_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "completed", "total", "score"])

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)

    return score
