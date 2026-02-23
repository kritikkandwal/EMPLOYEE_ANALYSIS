import os
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from utils.helpers import calculate_trend, generate_ai_message


class ProductivityForecaster:
    """
    Optimized Productivity Forecaster
    - Caches CSV data in memory
    - Caches per-user prediction results
    - Avoids retraining model per request
    """

    CACHE_TTL = 300  # 5 minutes

    def __init__(self, data_path="data/productivity/"):
        self.data_path = data_path
        os.makedirs(self.data_path, exist_ok=True)

        self.daily_file = os.path.join(self.data_path, "productivity_daily.csv")

        if not os.path.exists(self.daily_file):
            df = pd.DataFrame(
                columns=["user_id", "date", "score", "completed", "total"]
            )
            df.to_csv(self.daily_file, index=False)

        # --- CACHING ---
        self._data_cache = None
        self._data_cache_time = 0

        self._prediction_cache: Dict[int, Dict[str, Any]] = {}
        self._prediction_cache_time: Dict[int, float] = {}

        self._lock = threading.Lock()

    # -------------------------------------------------
    # INTERNAL: LOAD DATA WITH TTL CACHE
    # -------------------------------------------------
    def _load_daily_data(self) -> pd.DataFrame:
        now = time.time()

        if (
            self._data_cache is not None
            and now - self._data_cache_time < self.CACHE_TTL
        ):
            return self._data_cache

        df = pd.read_csv(self.daily_file)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"]).dt.date

        self._data_cache = df
        self._data_cache_time = now

        return df

    def _save_daily_data(self, df):
        df.to_csv(self.daily_file, index=False)

        # Invalidate cache
        self._data_cache = df
        self._data_cache_time = time.time()

        # Clear prediction cache since data changed
        self._prediction_cache.clear()
        self._prediction_cache_time.clear()

    # -------------------------------------------------
    # UPDATE TODAY
    # -------------------------------------------------
    def update_today(self, user_id: int, today_score=None, completed=None, total=None):
        with self._lock:
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
                                    "score": float(today_score or 0),
                                    "completed": int(completed or 0),
                                    "total": int(total or 0),
                                }
                            ]
                        ),
                    ],
                    ignore_index=True,
                )

            self._save_daily_data(df)

    # -------------------------------------------------
    # TREND DATA (NO REPEATED RETRAINING PER REQUEST)
    # -------------------------------------------------
    def _prepare_series(self, user_id):
        df = self._load_daily_data()
        df = df[df["user_id"] == user_id]

        if df.empty:
            return df

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

        history_df["idx"] = np.arange(len(history_df))
        history_df["dow"] = pd.to_datetime(history_df["date"]).dt.weekday

        X = history_df[["idx", "dow"]].values
        y = history_df["score"].astype(float).values

        if len(history_df) < 5:
            avg = float(np.mean(y))
            last_date = pd.to_datetime(history_df["date"].iloc[-1]).date()

            forecast_dates = [
                (last_date + timedelta(days=i)).isoformat()
                for i in range(1, horizon + 1)
            ]
            forecast_scores = [round(avg)] * horizon

            return {
                "history": {
                    "dates": history_df["date"].astype(str).tolist(),
                    "scores": y.round().tolist(),
                },
                "forecast": {"dates": forecast_dates, "scores": forecast_scores},
            }

        # Train model ONCE per call (data cached, so cheap)
        model = LinearRegression()
        model.fit(X, y)

        last_idx = int(history_df["idx"].iloc[-1])
        last_date = pd.to_datetime(history_df["date"].iloc[-1]).date()

        history_dates = history_df["date"].astype(str).tolist()
        history_scores = y.round().tolist()

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

    # -------------------------------------------------
    # PREDICTION SUMMARY WITH PER-USER CACHE
    # -------------------------------------------------
    def get_prediction_summary(self, user_id, today_score=None, completed=None, total=None):

        now = time.time()

        # Return cached result if fresh
        if (
            user_id in self._prediction_cache
            and now - self._prediction_cache_time[user_id] < self.CACHE_TTL
        ):
            return self._prediction_cache[user_id]

        if today_score is not None or completed is not None or total is not None:
            self.update_today(user_id, today_score, completed, total)

        trend = self.get_trend_data(user_id)

        history_scores = trend["history"]["scores"]
        forecast_scores = trend["forecast"]["scores"]

        if not history_scores or not forecast_scores:
            result = {
                "tomorrow_score": None,
                "next_7_days": [],
                "confidence": 0.5,
                "recommendation": "Not enough data.",
                "trend": trend,
            }
        else:
            tomorrow = forecast_scores[0]
            next_7 = forecast_scores

            current = float(history_scores[-1])
            prev = float(history_scores[-2]) if len(history_scores) > 1 else current

            trend_label = calculate_trend(current, prev)
            ai_msg = generate_ai_message(current, trend_label, {"focus_ratio": 0.8})

            std = float(np.std(history_scores))
            confidence = 1.0 - min(std / 100, 0.6)

            result = {
                "tomorrow_score": tomorrow,
                "next_7_days": next_7,
                "confidence": round(confidence, 2),
                "recommendation": ai_msg,
                "trend": trend,
            }

        # Store in cache
        self._prediction_cache[user_id] = result
        self._prediction_cache_time[user_id] = now

        return result