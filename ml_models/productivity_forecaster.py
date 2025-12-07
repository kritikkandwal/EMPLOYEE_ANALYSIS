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
    ML + data manager for daily productivity history and forecasting.
    
    Storage:
      data/productivity_daily.csv

    Columns:
      user_id (int)
      date (YYYY-MM-DD)
      score (0-100)
      completed (int)
      total (int)
    """

    def __init__(self, data_path: str = "data/"):
        self.data_path = data_path
        os.makedirs(self.data_path, exist_ok=True)
        self.daily_file = os.path.join(self.data_path, "productivity_daily.csv")

        # Ensure file exists
        if not os.path.exists(self.daily_file):
            df = pd.DataFrame(
                columns=["user_id", "date", "score", "completed", "total"]
            )
            df.to_csv(self.daily_file, index=False)

    # ---------------------------
    # Internal helpers
    # ---------------------------

    def _load_daily_data(self) -> pd.DataFrame:
        try:
            df = pd.read_csv(self.daily_file)
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"]).dt.date
            return df
        except Exception:
            df = pd.DataFrame(
                columns=["user_id", "date", "score", "completed", "total"]
            )
            df.to_csv(self.daily_file, index=False)
            return df

    # def update_today(self, user_id, date, completed, total, score):
    #     df = self._load_daily_data(user_id)

    #     df.loc[df["date"] == date, ["score", "completed", "total"]] = [
    #         score, completed, total
    #     ]

    #     self._save_daily_data(user_id, df)

    
    def _save_daily_data(self, df: pd.DataFrame):
        df.to_csv(self.daily_file, index=False)

    def _ensure_user_history(self, user_id: int, days: int = 365):
        """
        Generate synthetic history ONLY for days without real task data.
        Today is NEVER synthetic.
        """
        df = self._load_daily_data()
        user_df = df[df["user_id"] == user_id]

        today = datetime.utcnow().date()

        existing_dates = set(user_df["date"]) if not user_df.empty else set()

        synthetic_rows = []

        # Generate synthetic for up to 1 full year
        for i in range(days):
            date = today - timedelta(days=i)

            # NEVER generate synthetic for today
            if date == today:
                continue

            # If real data exists → DO NOT generate synthetic
            if date in existing_dates:
                continue

            # Create a reasonable synthetic pattern
            base = 70
            if date.weekday() >= 5:  # Weekend
                base -= 10

            noise = np.random.normal(0, 12)
            score = int(np.clip(base + noise, 35, 95))

            total_tasks = np.random.randint(4, 10)
            completed = int(round(score / 100 * total_tasks))

            synthetic_rows.append({
                "user_id": user_id,
                "date": date,
                "score": score,
                "completed": completed,
                "total": total_tasks
            })

        if synthetic_rows:
            df = pd.concat([df, pd.DataFrame(synthetic_rows)], ignore_index=True)
            self._save_daily_data(df)




    # ---------------------------
    # Public operations
    # ---------------------------

    def update_today(
        self,
        user_id: int,
        today_score: Optional[float] = None,
        completed: Optional[int] = None,
        total: Optional[int] = None,
    ):
        """
        Upsert today's record using real data from tasks / frontend.
        """
        df = self._load_daily_data()
        today = datetime.utcnow().date()

        mask = (df["user_id"] == user_id) & (df["date"] == today)
        # If already present, update; else create
        if mask.any():
            idx = df[mask].index[0]
            if today_score is not None:
                df.at[idx, "score"] = float(today_score)
            if completed is not None:
                df.at[idx, "completed"] = int(completed)
            if total is not None:
                df.at[idx, "total"] = int(total)
        else:
            # If not provided, use fallback
            if total is None:
                total = 6
            if completed is None:
                completed = max(0, min(total, int(round((today_score or 70) / 100 * total))))
            if today_score is None:
                today_score = (completed / max(total, 1)) * 100

            df = pd.concat(
                [
                    df,
                    pd.DataFrame(
                        [
                            {
                                "user_id": user_id,
                                "date": today,
                                "score": float(today_score),
                                "completed": int(completed),
                                "total": int(total),
                            }
                        ]
                    ),
                ],
                ignore_index=True,
            )

        self._save_daily_data(df)

    def get_monthly_stats(
        self,
        user_id: int,
        year: Optional[int] = None,
        month: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Return per-day productivity stats and summary.

        If month is None → returns all days of the year.
        """
        self._ensure_user_history(user_id)
        df = self._load_daily_data()
        if df.empty:
            return {"by_date": {}, "summary": {}}

        df = df[df["user_id"] == user_id].copy()
        df["date"] = pd.to_datetime(df["date"]).dt.date

        if year is None:
            year = datetime.utcnow().year
        df = df[df["date"].apply(lambda d: d.year == year)]

        if month is not None:
            df = df[df["date"].apply(lambda d: d.month == month)]

        if df.empty:
            return {"by_date": {}, "summary": {}}

        # Per-day dict
        by_date: Dict[str, Any] = {}
        for _, row in df.iterrows():
            date_str = row["date"].isoformat()
            score = float(row["score"])
            level = "LOW"
            if score >= 80:
                level = "HIGH"
            elif score >= 40:
                level = "MEDIUM"

            by_date[date_str] = {
                "date": date_str,
                "score": round(score),
                "level": level,
                "completed": int(row.get("completed", 0) or 0),
                "total": int(row.get("total", 0) or 0),
            }

        scores = df["score"].values
        avg_score = float(np.mean(scores))
        best_idx = int(np.argmax(scores))
        worst_idx = int(np.argmin(scores))

        best_day = df.iloc[best_idx]["date"].isoformat()
        worst_day = df.iloc[worst_idx]["date"].isoformat()

        # Current streak = consecutive days (most recent backwards) with score > 0
        sorted_df = df.sort_values("date")
        streak = 0
        for _, row in sorted_df[::-1].iterrows():
            if row["score"] > 0:
                streak += 1
            else:
                break

        summary = {
            "year": year,
            "month": month,
            "average_score": round(avg_score, 1),
            "best_day": best_day,
            "worst_day": worst_day,
            "days_tracked": int(len(df)),
            "current_streak": streak,
        }

        return {"by_date": by_date, "summary": summary}

    def _prepare_series(self, user_id: int) -> pd.DataFrame:
        self._ensure_user_history(user_id)
        df = self._load_daily_data()
        df = df[df["user_id"] == user_id].copy()
        if df.empty:
            return df

        df["date"] = pd.to_datetime(df["date"]).dt.date
        df = df.sort_values("date")
        return df

    def get_trend_data(
        self, user_id: int, history_days: int = 30, horizon: int = 7
    ) -> Dict[str, Any]:
        """
        Returns last `history_days` scores and next `horizon` days forecast.
        """
        df = self._prepare_series(user_id)
        if df.empty:
            return {
                "history": {"dates": [], "scores": []},
                "forecast": {"dates": [], "scores": []},
            }

        # Take last history_days
        history_df = df.tail(history_days).copy()
        history_df.reset_index(drop=True, inplace=True)

        # Build simple supervised features: day index, day_of_week
        history_df["idx"] = np.arange(len(history_df))
        history_df["dow"] = history_df["date"].apply(lambda d: d.weekday())
        X = history_df[["idx", "dow"]].values
        y = history_df["score"].values

        # If not enough data, fallback to naive model
        if len(history_df) < 5:
            last_date = history_df["date"].iloc[-1]
            history_dates = [d.isoformat() for d in history_df["date"]]
            history_scores = [round(float(s)) for s in y]

            forecast_dates = []
            forecast_scores = []
            avg = float(np.mean(y))
            for i in range(1, horizon + 1):
                d = last_date + timedelta(days=i)
                forecast_dates.append(d.isoformat())
                forecast_scores.append(round(avg))

            return {
                "history": {"dates": history_dates, "scores": history_scores},
                "forecast": {"dates": forecast_dates, "scores": forecast_scores},
            }

        model = RandomForestRegressor(n_estimators=80, random_state=42)
        model.fit(X, y)

        last_idx = int(history_df["idx"].iloc[-1])
        last_date = history_df["date"].iloc[-1]

        history_dates = [d.isoformat() for d in history_df["date"]]
        history_scores = [round(float(s)) for s in y]

        forecast_dates: List[str] = []
        forecast_scores: List[int] = []

        for i in range(1, horizon + 1):
            future_idx = last_idx + i
            future_date = last_date + timedelta(days=i)
            dow = future_date.weekday()
            pred = float(model.predict(np.array([[future_idx, dow]]))[0])
            forecast_dates.append(future_date.isoformat())
            forecast_scores.append(int(round(np.clip(pred, 0, 100))))

        return {
            "history": {"dates": history_dates, "scores": history_scores},
            "forecast": {"dates": forecast_dates, "scores": forecast_scores},
        }

    def get_prediction_summary(
        self,
        user_id: int,
        today_score: Optional[float] = None,
        completed: Optional[int] = None,
        total: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        High-level AI predictions block:
          - tomorrow score
          - 7-day trend
          - streak prediction  (FIXED)
          - workload risk
          - recommended focus area
          - confidence
        """

        # Update today's real data if received
        if today_score is not None or completed is not None or total is not None:
            self.update_today(
                user_id,
                today_score=today_score,
                completed=completed,
                total=total
            )

        # Get trend + forecast data
        trend_data = self.get_trend_data(user_id, history_days=30, horizon=7)
        history_scores = np.array(trend_data["history"]["scores"], dtype=float) if trend_data["history"]["scores"] else np.array([])
        forecast_scores = np.array(trend_data["forecast"]["scores"], dtype=float) if trend_data["forecast"]["scores"] else np.array([])

        # If insufficient data
        if history_scores.size == 0 or forecast_scores.size == 0:
            return {
                "tomorrow_score": None,
                "next_7_days": [],
                "streak_prediction": {
                    "current": 0,
                    "continue_probability": 0,
                    "expected_duration": 0,
                    "health": 0,
                    "message": "Not enough data yet."
                },
                "workload_risk": {"label": "unknown", "description": "Start logging tasks to get predictions"},
                "recommendation": "Add more daily tasks so the AI can learn your pattern.",
                "focus_area": "consistency",
                "confidence": 0.5,
                "trend": trend_data
            }

        # -------------------------------
        # TOMORROW SCORE
        # -------------------------------
        tomorrow_score = float(forecast_scores[0])
        next_7 = [float(s) for s in forecast_scores.tolist()]

        # -------------------------------
        # STREAK PREDICTION (FIXED)
        # -------------------------------
        # Calculate current streak from history (score > 0)
        df = self._prepare_series(user_id)
        df_sorted = df.sort_values("date")
        current_streak = 0
        for _, row in df_sorted[::-1].iterrows():
            if row["score"] > 0:
                current_streak += 1
            else:
                break

        # Probability streak continues = tomorrow productivity probability
        continue_probability = int(np.clip(tomorrow_score, 0, 100))

        # Expected duration = number of days forecast >= 70% 
        expected_duration = int(np.sum(forecast_scores >= 70))

        # Streak health = normalized historical average
        historical_avg = float(np.mean(history_scores))
        streak_health = int(np.clip(historical_avg, 0, 100))

        streak_prediction = {
            "current": current_streak,
            "continue_probability": continue_probability,
            "expected_duration": expected_duration,
            "health": streak_health,
            "message": f"Your streak is expected to continue for {expected_duration} more days."
        }

        # -------------------------------
        # WORKLOAD RISK
        # -------------------------------
        historical_std = float(np.std(history_scores))

        if historical_avg > 82 and historical_std < 8:
            workload_label = "overwork"
            workload_desc = "High sustained productivity may indicate overwork. Plan recovery windows."
        elif historical_avg < 55:
            workload_label = "underwork"
            workload_desc = "Your average productivity is low. Time to re-structure your day."
        else:
            workload_label = "balanced"
            workload_desc = "Your workload looks balanced. Maintain your current pacing."

        # Confidence score
        if historical_std == 0:
            confidence = 0.9
        else:
            confidence = float(np.clip(1.0 - (historical_std / 100.0), 0.5, 0.95))

        # -------------------------------
        # AI Message & Focus Area
        # -------------------------------
        metrics = {
            "focus_ratio": 0.8,
            "task_efficiency": np.clip(historical_avg, 0, 100),
        }

        current_score = float(history_scores[-1])
        prev_score = float(history_scores[-2]) if len(history_scores) > 1 else current_score
        trend = calculate_trend(current_score, prev_score)
        ai_message = generate_ai_message(current_score, trend, metrics)

        if workload_label == "overwork":
            focus_area = "recovery"
        elif workload_label == "underwork":
            focus_area = "execution"
        elif expected_duration >= 5:
            focus_area = "stretch-goals"
        else:
            focus_area = "consistency"

        # -------------------------------
        # FINAL RETURN DICT
        # -------------------------------
        return {
            "tomorrow_score": round(tomorrow_score),
            "next_7_days": [round(x) for x in next_7],
            "streak_prediction": streak_prediction,
            "workload_risk": {
                "label": workload_label,
                "description": workload_desc,
            },
            "recommendation": ai_message,
            "focus_area": focus_area,
            "confidence": round(confidence, 2),
            "trend": trend_data,
        }

