import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from .lr_model import AttendanceLinearRegression
from .prophet_model import AttendanceProphet
from .lstm_model import AttendanceLSTM

class AttendancePredictor:
    def __init__(self, data_path='data/attendance/attendance.csv'):
        self.data_path = data_path
        self.lr_model = AttendanceLinearRegression()
        self.prophet_model = AttendanceProphet()
        self.lstm_model = AttendanceLSTM()
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        
    def load_data(self):
        """Load attendance data from CSV"""
        try:
            if os.path.exists(self.data_path):
                df = pd.read_csv(self.data_path)
                df['date'] = pd.to_datetime(df['date'])
                return df
            else:
                return self.create_sample_data()
        except Exception as e:
            print(f"Error loading data: {e}")
            return self.create_sample_data()
    
    def create_sample_data(self):
        """Create sample data if CSV doesn't exist"""
        dates = pd.date_range(start='2024-01-01', end=datetime.now().date())
        
        # Create realistic attendance pattern
        np.random.seed(42)
        base_attendance = 0.85  # 85% base attendance
        
        # Weekly pattern (lower on weekends)
        day_of_week_effect = [0.0, 0.0, 0.02, 0.03, 0.02, -0.15, -0.20]
        
        # Monthly trend (slight improvement over time)
        monthly_trend = np.linspace(0, 0.1, len(dates))
        
        # Random noise
        noise = np.random.normal(0, 0.05, len(dates))
        
        attendance = []
        for i, date in enumerate(dates):
            day_effect = day_of_week_effect[date.weekday()]
            trend_effect = monthly_trend[i]
            
            prob = base_attendance + day_effect + trend_effect + noise[i]
            # Ensure probability is between 0 and 1
            prob = max(0.1, min(0.98, prob))
            
            # Simulate actual attendance (1 for present, 0 for absent)
            attended = 1 if np.random.random() < prob else 0
            attendance.append(attended)
        
        df = pd.DataFrame({
            'date': dates,
            'attendance': attendance,
            'day_of_week': [d.weekday() for d in dates],
            'month': [d.month for d in dates]
        })
        
        # Save sample data
        df.to_csv(self.data_path, index=False)
        print(f"Created sample data at {self.data_path}")
        
        return df
    
    def train_all_models(self):
        """Train all three ML models"""
        df = self.load_data()
        
        results = {
            'lr_trained': self.lr_model.train(df),
            'prophet_trained': self.prophet_model.train(df),
            'lstm_trained': self.lstm_model.train(df)
        }
        
        return results
    
    def predict_all(self):
        """Get predictions from all three models"""
        df = self.load_data()
        
        # Linear Regression prediction (tomorrow)
        lr_pred = self.lr_model.predict(df)
        
        # Prophet predictions (next 7 days)
        prophet_preds, forecast_plot = self.prophet_model.predict(df, days=7)
        
        # LSTM prediction (tomorrow)
        lstm_pred = self.lstm_model.predict(df)
        
        # Calculate streak forecast
        streak_forecast = self.calculate_streak_forecast(df, lr_pred)
        
        # Calculate absence likelihood
        absence_likelihood = self.calculate_absence_likelihood(lr_pred, lstm_pred, prophet_preds[0])
        
        return {
            'lr_prediction': round(lr_pred, 3),
            'prophet_prediction': round(prophet_preds[0], 3),
            'lstm_prediction': round(lstm_pred, 3),
            'next_week_forecast': [round(p, 3) for p in prophet_preds],
            'forecast_plot': forecast_plot,
            'streak_prediction': streak_forecast,
            'absence_likelihood': round(absence_likelihood, 3),
            'average_prediction': round((lr_pred + lstm_pred + prophet_preds[0]) / 3, 3)
        }
    
    def calculate_streak_forecast(self, df, tomorrow_pred):
        """
        REAL streak forecasting:
        - current_streak = count of consecutive present days
        - tomorrow_pred = ML probability of being present tomorrow (0–1)
        - probability_continue = tomorrow_pred * 100
        - expected_end_in = geometric model (probability-driven)
        """
        # Extract last 14 days (better streak window)
        recent = df['attendance'].tail(14).values
    
        # Calculate REAL current streak
        current_streak = 0
        for a in reversed(recent):
            if a == 1:
                current_streak += 1
            else:
                break
            
        # Probability of continuing streak
        probability_continue = round(float(tomorrow_pred) * 100, 1)
    
        # Expected continuation (Geometric expectation)
        # formula: E = p / (1 - p)
        p = float(tomorrow_pred)
        if p >= 0.99:
            expected_more_days = 10
        else:
            expected_more_days = round(p / (1 - p), 1)
    
        return {
            "current_streak": current_streak,
            "probability_continue": probability_continue,
            "expected_end_in": expected_more_days
        }


    def calculate_absence_likelihood(self, lr_pred, lstm_pred, prophet_pred):
        """Calculate absence likelihood from all predictions"""
        avg_pred = (lr_pred + lstm_pred + prophet_pred) / 3
        absence_likelihood = 1 - avg_pred  # Convert to absence probability
        return absence_likelihood

# Global predictor instance
predictor = AttendancePredictor()