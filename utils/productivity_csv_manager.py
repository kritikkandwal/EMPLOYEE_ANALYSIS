import pandas as pd
from datetime import date

CSV_PATH = "data/productivity/productivity_daily.csv"


def update_today_productivity(user_id, completed, total):

    today = date.today().strftime("%Y-%m-%d")

    if total == 0:
        score = 0
    else:
        score = int((completed / total) * 100)

    df = pd.read_csv(CSV_PATH)

    if today in df["date"].values:

        df.loc[df["date"] == today, "completed"] = completed
        df.loc[df["date"] == today, "total"] = total
        df.loc[df["date"] == today, "score"] = score

    else:

        new_row = {
            "user_id": user_id,
            "date": today,
            "score": score,
            "completed": completed,
            "total": total
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    df.to_csv(CSV_PATH, index=False)

    return score