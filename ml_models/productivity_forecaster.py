# ml_models/productivity_forecaster.py

import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from utils.helpers import calculate_trend, generate_ai_message


class ProductivityForecaster:
    """
    ML forecaster that uses ONLY real CSV data.

    CSV: data/productivity/productivity_daily.csv

    Columns:
        user_id, date, score, completed, total
    """

    def __init__(self, data_path="data/productivity/"):
        self.data_path = data_path
        os.makedirs(self.data_path, exist_ok=True)

        self.daily_file = os.path.join(self.data_path, "productivity_daily.csv")

        if not os.path.exists(self.daily_file):
            df = pd.DataFrame(
                columns=["user_id", "date", "score", "completed", "total"]
            )
            df.to_csv(self.daily_file, index=False)

    # -------------------------
    # DATA LOADING / SAVING
    # -------------------------
    def _load_daily_data(self) -> pd.DataFrame:
        try:
            df = pd.read_csv(self.daily_file)
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"]).dt.date
            return df
        except:
            df = pd.DataFrame(columns=["user_id", "date", "score", "completed", "total"])
            df.to_csv(self.daily_file, index=False)
            return df

    def _save_daily_data(self, df):
        df.to_csv(self.daily_file, index=False)

    # -------------------------
    # UPDATE TODAY → real data only
    # -------------------------
    def update_today(self, user_id: int, today_score=None, completed=None, total=None):
        df = self._load_daily_data()
        today = datetime.utcnow().date()

        mask = (df["user_id"] == user_id) & (df["date"] == today)

        if mask.any():
            idx = df[mask].index[0]
            if today_score is not None:
                df.at[idx, "score"] = float(today_score)
            if completed is not None:
                df.at[idx, "completed"] = int(completed)
            if total is not None:
                df.at[idx, "total"] = int(total)
        else:
            if today_score is None and completed is not None and total is not None:
                today_score = (completed / max(total, 1)) * 100

            df = pd.concat(
                [
                    df,
                    pd.DataFrame(
                        [
                            {
                                "user_id": user_id,
                                "date": today,
                                "score": float(today_score) if today_score else 0,
                                "completed": int(completed or 0),
                                "total": int(total or 0),
                            }
                        ]
                    ),
                ],
                ignore_index=True,
            )

        self._save_daily_data(df)

    # -------------------------
    # MONTHLY STATS (for calendar)
    # -------------------------
    def get_monthly_stats(self, user_id, year=None, month=None):
        df = self._load_daily_data()

        df = df[df["user_id"] == user_id]

        if df.empty:
            return {"by_date": {}, "summary": {}}

        df["date"] = pd.to_datetime(df["date"]).dt.date

        if year is None:
            year = datetime.utcnow().year

        df = df[df["date"].apply(lambda d: d.year == year)]

        if month:
            df = df[df["date"].apply(lambda d: d.month == month)]

        if df.empty:
            return {"by_date": {}, "summary": {}}

        # --- daily mapping ---
        by_date = {}
        for _, row in df.iterrows():
            date_str = row["date"].isoformat()
            score = float(row["score"])

            if score >= 80:
                level = "HIGH"
            elif score >= 40:
                level = "MEDIUM"
            else:
                level = "LOW"

            by_date[date_str] = {
                "date": date_str,
                "score": round(score),
                "level": level,
                "completed": int(row["completed"]),
                "total": int(row["total"]),
            }

        # summary
        scores = df["score"].values
        avg = float(np.mean(scores))

        best = df.iloc[int(np.argmax(scores))]["date"].isoformat()
        worst = df.iloc[int(np.argmin(scores))]["date"].isoformat()

        # streak tracking
        streak = 0
        for _, row in df.sort_values("date")[::-1].iterrows():
            if row["score"] > 0:
                streak += 1
            else:
                break

        summary = {
            "year": year,
            "month": month,
            "average_score": round(avg, 1),
            "best_day": best,
            "worst_day": worst,
            "days_tracked": len(df),
            "current_streak": streak,
        }

        return {"by_date": by_date, "summary": summary}

    # -------------------------
    # TREND DATA (history + forecast)
    # -------------------------
    def _prepare_series(self, user_id):
        df = self._load_daily_data()
        df = df[df["user_id"] == user_id]

        if df.empty:
            return df

        df["date"] = pd.to_datetime(df["date"]).dt.date
        df = df.sort_values("date")
        return df

    def get_trend_data(self, user_id, history_days=30, horizon=7):
        df = self._prepare_series(user_id)

        if df.empty:
            return {
                "history": {"dates": [], "scores": []},
                "forecast": {"dates": [], "scores": []},
            }

        history_df = df.tail(history_days).copy()
        history_df.reset_index(drop=True, inplace=True)

        # features
        history_df["idx"] = np.arange(len(history_df))
        history_df["dow"] = history_df["date"].apply(lambda d: d.weekday())

        X = history_df[["idx", "dow"]].values
        y = history_df["score"].astype(float).values

        # not enough data → no model
        if len(history_df) < 5:
            last_date = history_df["date"].iloc[-1]

            avg = float(np.mean(y))
            forecast_dates = [(last_date + timedelta(days=i)).isoformat() for i in range(1, horizon + 1)]
            forecast_scores = [round(avg)] * horizon

            return {
                "history": {
                    "dates": [d.isoformat() for d in history_df["date"]],
                    "scores": [round(float(s)) for s in y],
                },
                "forecast": {"dates": forecast_dates, "scores": forecast_scores},
            }

        # TRAIN MODEL
        model = RandomForestRegressor(n_estimators=120, random_state=42)
        model.fit(X, y)

        last_idx = int(history_df["idx"].iloc[-1])
        last_date = history_df["date"].iloc[-1]

        history_dates = [d.isoformat() for d in history_df["date"]]
        history_scores = [round(float(s)) for s in y]

        forecast_dates = []
        forecast_scores = []

        for i in range(1, horizon + 1):
            idx = last_idx + i
            future_date = last_date + timedelta(days=i)
            dow = future_date.weekday()

            pred = float(model.predict([[idx, dow]])[0])
            pred = int(round(np.clip(pred, 0, 100)))

            forecast_dates.append(future_date.isoformat())
            forecast_scores.append(pred)

        return {
            "history": {"dates": history_dates, "scores": history_scores},
            "forecast": {"dates": forecast_dates, "scores": forecast_scores},
        }

    # -------------------------
    # PREDICTION SUMMARY
    # -------------------------
    def get_prediction_summary(self, user_id, today_score=None, completed=None, total=None):

        # Update today's real data
        if today_score is not None or completed is not None or total is not None:
            self.update_today(user_id, today_score, completed, total)

        trend = self.get_trend_data(user_id)

        history_scores = trend["history"]["scores"]
        forecast_scores = trend["forecast"]["scores"]

        if len(history_scores) == 0 or len(forecast_scores) == 0:
            return {
                "tomorrow_score": None,
                "next_7_days": [],
                "confidence": 0.5,
                "recommendation": "Not enough data.",
                "trend": trend,
            }

        tomorrow = forecast_scores[0]
        next_7 = forecast_scores

        # AI message
        current = float(history_scores[-1])
        prev = float(history_scores[-2]) if len(history_scores) > 1 else current
        trend_label = calculate_trend(current, prev)
        ai_msg = generate_ai_message(current, trend_label, {"focus_ratio": 0.8})

        # confidence
        std = float(np.std(history_scores))
        confidence = 1.0 - min(std / 100, 0.6)

        return {
            "tomorrow_score": tomorrow,
            "next_7_days": next_7,
            "confidence": round(confidence, 2),
            "recommendation": ai_msg,
            "trend": trend,
        }
