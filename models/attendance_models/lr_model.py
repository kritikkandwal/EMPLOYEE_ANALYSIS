import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
import joblib
import os
from datetime import datetime, timedelta

class AttendanceLinearRegression:
    def __init__(self, models_path='models/attendance_models/trained_models/'):
        self.models_path = models_path
        self.model = None
        self.is_trained = False
        os.makedirs(models_path, exist_ok=True)
    
    def create_features(self, df):
        """Create time series features for linear regression"""
        df = df.copy()
        
        # Lag features
        df['lag_1'] = df['attendance'].shift(1)
        df['lag_7'] = df['attendance'].shift(7)
        df['lag_30'] = df['attendance'].shift(30)
        
        # Rolling statistics
        df['rolling_mean_7'] = df['attendance'].rolling(window=7).mean()
        df['rolling_std_7'] = df['attendance'].rolling(window=7).std()
        df['rolling_mean_30'] = df['attendance'].rolling(window=30).mean()
        
        # Date-based features
        df['day_of_week'] = df['date'].dt.dayofweek
        df['day_of_month'] = df['date'].dt.day
        df['is_weekend'] = df['date'].dt.dayofweek.isin([5, 6]).astype(int)
        df['month'] = df['date'].dt.month
        df['week_of_year'] = df['date'].dt.isocalendar().week
        
        # Trend
        df['trend'] = range(len(df))
        
        return df
    
    def prepare_data(self, df):
        """Prepare data for training"""
        df = self.create_features(df)
        df = df.dropna()  # Remove rows with NaN from lag features
        
        # Features for model
        feature_columns = [
            'lag_1', 'lag_7', 'lag_30', 
            'rolling_mean_7', 'rolling_std_7', 'rolling_mean_30',
            'day_of_week', 'day_of_month', 'is_weekend', 'month', 'week_of_year', 'trend'
        ]
        
        X = df[feature_columns]
        y = df['attendance']
        
        return X, y, feature_columns
    
    def train(self, df):
        """Train the linear regression model"""
        try:
            X, y, feature_columns = self.prepare_data(df)
            
            if len(X) < 10:
                print("Insufficient data for training")
                return False
            
            self.model = LinearRegression()
            self.model.fit(X, y)
            
            # Make predictions on training data for evaluation
            y_pred = self.model.predict(X)
            mae = mean_absolute_error(y, y_pred)
            
            print(f"Linear Regression trained - MAE: {mae:.4f}")
            
            # Save model
            joblib.dump({
                'model': self.model,
                'feature_columns': feature_columns,
                'mae': mae,
                'trained_at': datetime.now()
            }, os.path.join(self.models_path, 'linear_regression_model.pkl'))
            
            self.is_trained = True
            return True
            
        except Exception as e:
            print(f"Error training Linear Regression: {e}")
            return False
    
    def predict(self, df):
        """Predict next day's attendance probability"""
        if not self.is_trained:
            self.load_model()
        
        if self.model is None:
            return 0.75  # Default fallback
        
        try:
            # Prepare latest data for prediction
            df_features = self.create_features(df)
            latest = df_features.iloc[-1:]
            
            # Get feature columns used during training
            model_data = joblib.load(os.path.join(self.models_path, 'linear_regression_model.pkl'))
            feature_columns = model_data['feature_columns']
            
            # Ensure we have all required features
            X_pred = latest[feature_columns]
            
            prediction = self.model.predict(X_pred)[0]
            # Convert to probability between 0 and 1
            probability = max(0, min(1, prediction))
            
            return probability
            
        except Exception as e:
            print(f"Error in Linear Regression prediction: {e}")
            return 0.75
    
    def load_model(self):
        """Load trained model"""
        model_path = os.path.join(self.models_path, 'linear_regression_model.pkl')
        if os.path.exists(model_path):
            model_data = joblib.load(model_path)
            self.model = model_data['model']
            self.is_trained = True