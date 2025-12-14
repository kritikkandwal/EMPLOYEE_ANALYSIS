import pandas as pd

ATTENDANCE_CSV = "data/attendance/attendance_generated.csv"
PRODUCTIVITY_CSV = "data/productivity/productivity_daily.csv"


def load_dashboard_data():
    """
    Loads dashboard analytics strictly from CSV files.
    No database. No ML models. No side effects.
    """

    # ---------------------------
    # LOAD CSV DATA
    # ---------------------------
    attendance_df = pd.read_csv(
        ATTENDANCE_CSV,
        parse_dates=["date"]
    )

    productivity_df = pd.read_csv(
        PRODUCTIVITY_CSV,
        parse_dates=["date"]
    )

    # Normalize date format for frontend (ISO)
    attendance_df["date"] = attendance_df["date"].dt.strftime("%Y-%m-%d")
    productivity_df["date"] = productivity_df["date"].dt.strftime("%Y-%m-%d")

    # ---------------------------
    # KPI CALCULATIONS
    # ---------------------------
    total_days = len(attendance_df)
    present_days = attendance_df["attendance"].sum()

    attendance_rate = round((present_days / max(total_days, 1)) * 100, 1)
    total_hours = int(attendance_df["hours"].sum())

    avg_productivity = round(productivity_df["score"].mean(), 1)

    completion_ratio = round(
        (productivity_df["completed"].sum() /
         max(productivity_df["total"].sum(), 1)) * 100,
        1
    )

    # ---------------------------
    # TREND DATA (LAST 30 DAYS)
    # ---------------------------
    attendance_calendar = attendance_df.tail(30)[
        ["date", "attendance"]
    ].to_dict("records")

    hours_trend = attendance_df.tail(30)[
        ["date", "hours"]
    ].to_dict("records")

    productivity_trend = productivity_df.tail(30)[
        ["date", "score"]
    ].to_dict("records")

    task_completion = productivity_df.tail(30).assign(
        ratio=lambda df: (df["completed"] / df["total"]) * 100
    )[["date", "ratio"]].fillna(0).to_dict("records")

    # ---------------------------
    # ATTENDANCE CONSISTENCY (7-DAY ROLLING AVG)
    # ---------------------------
    att_sorted = attendance_df.copy()
    att_sorted["date"] = pd.to_datetime(att_sorted["date"])
    att_sorted = att_sorted.sort_values("date")

    att_sorted["attendance_7day_avg"] = (
        att_sorted["attendance"]
        .rolling(7, min_periods=1)
        .mean()
    )

    att_sorted["date"] = att_sorted["date"].dt.strftime("%Y-%m-%d")

    attendance_consistency = att_sorted.tail(30)[
        ["date", "attendance_7day_avg"]
    ].to_dict("records")

    # ---------------------------
    # CORRELATION (Hours vs Productivity)
    # ---------------------------
    merged_df = pd.merge(
        attendance_df.assign(date=pd.to_datetime(attendance_df["date"])),
        productivity_df.assign(date=pd.to_datetime(productivity_df["date"])),
        on="date",
        how="inner"
    )

    correlation = merged_df[["hours", "score"]].dropna().to_dict("records")

    # ---------------------------
    # WEEKLY INSIGHTS
    # ---------------------------
    merged_df["week"] = merged_df["date"].dt.strftime("%Y-W%U")

    weekly_insights = merged_df.groupby("week").agg(
        avg_hours=("hours", "mean"),
        avg_score=("score", "mean")
    ).round(1).reset_index().to_dict("records")

    # ---------------------------
    # FINAL PAYLOAD
    # ---------------------------
    return {
        "kpi": {
            "attendance_rate": attendance_rate,
            "productivity_avg": avg_productivity,
            "completion_ratio": completion_ratio,
            "total_hours": total_hours,
            "productivity_outlook": "Stable",
            "outlook_color": "#2ecc71"
        },
        "attendanceCalendar": attendance_calendar,
        "attendanceConsistency": attendance_consistency,
        "hoursTrend": hours_trend,
        "productivityTrend": productivity_trend,
        "taskCompletion": task_completion,
        "correlation": correlation,
        "weeklyInsights": weekly_insights
    }
