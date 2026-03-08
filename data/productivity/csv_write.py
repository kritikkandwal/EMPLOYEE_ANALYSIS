import csv
import os

CSV_PATH = "data/productivity/productivity_daily.csv"


def update_csv_for_day(date, completed, total):
    os.makedirs("data/productivity", exist_ok=True)

    score = 0
    if total > 0:
        score = round((completed / total) * 100)

    rows = []
    found = False

    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["date"] == date:
                    row["completed"] = completed
                    row["total"] = total
                    row["score"] = score
                    found = True
                rows.append(row)

    if not found:
        rows.append({
            "date": date,
            "completed": completed,
            "total": total,
            "score": score
        })

    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["date", "completed", "total", "score"]
        )
        writer.writeheader()
        writer.writerows(rows)

    return score