import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os


class AttendancePredictor:
    def __init__(self, data_path='data/attendance/attendance_generated.csv'):
        self.data_path = data_path

        self.lr_model = None
        self.prophet_model = None
        self.lstm_model = None

        os.makedirs(os.path.dirname(data_path), exist_ok=True)

    # -----------------------
    # DATA
    # -----------------------

    def load_data(self):
        if os.path.exists(self.data_path):
            df = pd.read_csv(self.data_path)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')

            def convert(att):
                if att == 1:
                    return 1.0
                elif att == 2:
                    return 0.5
                return 0.0

            df['attendance'] = df['attendance'].apply(convert)
            df['day_of_week'] = df['date'].dt.weekday
            df['month'] = df['date'].dt.month
            return df

        return self.create_sample_data()

    def create_sample_data(self):
        dates = pd.date_range(start='2024-01-01', end=datetime.now().date())
        attendance = np.random.binomial(1, 0.85, len(dates))

        df = pd.DataFrame({
            'date': dates,
            'attendance': attendance,
            'day_of_week': [d.weekday() for d in dates],
            'month': [d.month for d in dates]
        })

        df.to_csv(self.data_path, index=False)
        return df

    # -----------------------
    # LAZY LOAD MODELS
    # -----------------------

    def _load_lr(self):
        if self.lr_model is None:
            from .lr_model import AttendanceLinearRegression
            self.lr_model = AttendanceLinearRegression()

    def _load_prophet(self):
        if self.prophet_model is None:
            from .prophet_model import AttendanceProphet
            self.prophet_model = AttendanceProphet()

    def _load_lstm(self):
        if self.lstm_model is None:
            from .lstm_model import AttendanceLSTM
            self.lstm_model = AttendanceLSTM()

    # -----------------------
    # TRAIN
    # -----------------------

    def train_all_models(self):
        df = self.load_data()

        self._load_lr()
        self._load_prophet()
        self._load_lstm()

        return {
            "lr_trained": self.lr_model.train(df),
            "prophet_trained": self.prophet_model.train(df),
            "lstm_trained": self.lstm_model.train(df)
        }

    # -----------------------
    # PREDICT
    # -----------------------

    def predict_all(self):
        df = self.load_data()

        self._load_lr()
        self._load_prophet()
        self._load_lstm()

        lr_pred = self.lr_model.predict(df)
        prophet_preds, forecast_plot = self.prophet_model.predict(df, days=7)
        lstm_pred = self.lstm_model.predict(df)

        tomorrow = prophet_preds[0]

        ensemble = (lr_pred + lstm_pred + tomorrow) / 3

        absence_likelihood = 1 - ensemble

        streak_forecast = self.calculate_streak_forecast(df, ensemble)

        return {
            "lr_prediction": round(lr_pred, 3),
            "prophet_prediction": round(tomorrow, 3),
            "lstm_prediction": round(lstm_pred, 3),
            "next_week_forecast": [round(p, 3) for p in prophet_preds],
            "forecast_plot": forecast_plot,
            "streak_prediction": streak_forecast,
            "absence_likelihood": round(absence_likelihood, 3),
            "average_prediction": round(ensemble, 3)
        }

    # -----------------------
    # STREAK
    # -----------------------

    def calculate_streak_forecast(self, df, tomorrow_pred):
        recent = df['attendance'].tail(14).values

        current_streak = 0
        for a in reversed(recent):
            if a == 1:
                current_streak += 1
            else:
                break

        probability_continue = round(tomorrow_pred * 100, 1)

        p = tomorrow_pred
        expected_more_days = 10 if p >= 0.99 else round(p / (1 - p), 1)

        return {
            "current_streak": current_streak,
            "probability_continue": probability_continue,
            "expected_end_in": expected_more_days
        }


predictor = AttendancePredictor()