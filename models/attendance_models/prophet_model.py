import pandas as pd
import numpy as np
from prophet import Prophet
import joblib
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import base64
from io import BytesIO

class AttendanceProphet:
    def __init__(self, models_path='models/attendance_models/trained_models/'):
        self.models_path = models_path
        self.model = None
        self.is_trained = False
        os.makedirs(models_path, exist_ok=True)
    
    def prepare_data(self, df):
        """Prepare data for Prophet (requires 'ds' and 'y' columns)"""
        prophet_df = df[['date', 'attendance']].copy()
        prophet_df.columns = ['ds', 'y']
        prophet_df['ds'] = pd.to_datetime(prophet_df['ds'])
        return prophet_df
    
    def train(self, df):
        """Train the Prophet model"""
        try:
            if len(df) < 30:
                print("Insufficient data for Prophet training")
                return False
            
            prophet_df = self.prepare_data(df)
            
            # Initialize and configure Prophet
            self.model = Prophet(
                daily_seasonality=True,
                weekly_seasonality=True,
                yearly_seasonality=True,
                changepoint_prior_scale=0.05
            )
            
            # Add additional regressors if available
            if 'day_of_week' in df.columns:
                prophet_df['day_of_week'] = df['day_of_week']
                self.model.add_regressor('day_of_week')
            
            self.model.fit(prophet_df)
            
            # Save model
            joblib.dump({
                'model': self.model,
                'trained_at': datetime.now()
            }, os.path.join(self.models_path, 'prophet_model.pkl'))
            
            self.is_trained = True
            print("Prophet model trained successfully")
            return True
            
        except Exception as e:
            print(f"Error training Prophet model: {e}")
            return False
    
    def predict(self, df, days=7):
        """Predict next n days using Prophet"""
        if not self.is_trained:
            self.load_model()
        
        if self.model is None:
            # Return default predictions
            return [0.8] * days, None
        
        try:
            # Create future dataframe
            future = self.model.make_future_dataframe(periods=days)
            
            # Add regressors if they were used during training
            if 'day_of_week' in df.columns:
                future['day_of_week'] = future['ds'].dt.dayofweek
            
            # Make prediction
            forecast = self.model.predict(future)
            
            # Get the next 'days' predictions
            future_predictions = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(days)
            
            # Convert to probabilities (ensure between 0-1)
            predictions = [max(0, min(1, pred)) for pred in future_predictions['yhat'].values]
            
            # Generate forecast plot
            plot_base64 = self.generate_forecast_plot(forecast, df)
            
            return predictions, plot_base64
            
        except Exception as e:
            print(f"Error in Prophet prediction: {e}")
            return [0.8] * days, None
    
    def generate_forecast_plot(self, forecast, historical_df):
        """Generate forecast visualization as base64"""
        try:
            plt.figure(figsize=(12, 6))
            
            # Plot historical data
            historical_dates = pd.to_datetime(historical_df['date'])
            plt.plot(historical_dates, historical_df['attendance'], 
                    'b-', label='Historical Attendance', linewidth=2)
            
            # Plot forecast
            future_dates = forecast['ds'].tail(30)  # Last 30 days + forecast
            future_values = forecast['yhat'].tail(30)
            future_lower = forecast['yhat_lower'].tail(30)
            future_upper = forecast['yhat_upper'].tail(30)
            
            plt.plot(future_dates, future_values, 'r-', label='Forecast', linewidth=2)
            plt.fill_between(future_dates, future_lower, future_upper, 
                           alpha=0.2, color='red', label='Uncertainty')
            
            plt.axvline(x=pd.to_datetime('today'), color='gray', linestyle='--', 
                       label='Today')
            
            plt.title('7-Day Attendance Forecast with Prophet')
            plt.xlabel('Date')
            plt.ylabel('Attendance Probability')
            plt.legend()
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Convert to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return f"data:image/png;base64,{image_base64}"
            
        except Exception as e:
            print(f"Error generating forecast plot: {e}")
            return None
    
    def load_model(self):
        """Load trained model"""
        model_path = os.path.join(self.models_path, 'prophet_model.pkl')
        if os.path.exists(model_path):
            model_data = joblib.load(model_path)
            self.model = model_data['model']
            self.is_trained = True