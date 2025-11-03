import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
import os
from datetime import datetime, timedelta

class ProductivityPredictor:
    def __init__(self, models_path='data/trained_models/'):
        self.models_path = models_path
        self.weekly_model = None
        self.monthly_model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        
        # Create models directory if it doesn't exist
        os.makedirs(models_path, exist_ok=True)
    
    def engineer_features(self, user_data, historical_data):
        """Engineer features for the ML model"""
        features = {}
        
        # Monthly aggregate features
        features['avg_work_hours'] = historical_data['hours_worked'].mean()
        features['avg_focus_ratio'] = historical_data['focus_ratio'].mean()
        features['task_completion_rate'] = historical_data['tasks_completed'].sum() / historical_data['tasks_assigned'].sum()
        features['consistency_index'] = 100 - (historical_data['productivity_score'].std() * 10)
        
        # Temporal features
        weekly_scores = self._get_weekly_scores(historical_data)
        features['productivity_trend'] = self._calculate_trend(weekly_scores)
        features['last_week_momentum'] = weekly_scores[-1] - np.mean(weekly_scores)
        features['volatility'] = historical_data['productivity_score'].std()
        
        # Context features
        features['meeting_load'] = historical_data['meeting_hours'].sum() / historical_data['hours_worked'].sum()
        features['collaboration_intensity'] = historical_data['collaboration_score'].mean()
        
        return features
    
    def _get_weekly_scores(self, historical_data):
        """Calculate weekly productivity scores"""
        # Simplified implementation - in production, group by week
        if len(historical_data) >= 7:
            return [historical_data['productivity_score'].iloc[-7:].mean()]
        return [historical_data['productivity_score'].mean()]
    
    def _calculate_trend(self, weekly_scores):
        """Calculate productivity trend"""
        if len(weekly_scores) > 1:
            x = np.arange(len(weekly_scores))
            slope = np.polyfit(x, weekly_scores, 1)[0]
            return slope
        return 0
    
    def train(self, X, y):
        """Train the productivity prediction model"""
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train Random Forest model
        self.weekly_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        
        self.weekly_model.fit(X_scaled, y)
        self.is_trained = True
        
        # Save model
        joblib.dump({
            'model': self.weekly_model,
            'scaler': self.scaler
        }, os.path.join(self.models_path, 'productivity_model.pkl'))
    
    def predict(self, features):
        """Predict productivity score"""
        if not self.is_trained:
            self.load_model()
        
        if self.weekly_model:
            features_scaled = self.scaler.transform([features])
            prediction = self.weekly_model.predict(features_scaled)[0]
            return max(0, min(100, prediction))
        
        return 75.0  # Fallback prediction
    
    def load_model(self):
        """Load trained model"""
        model_path = os.path.join(self.models_path, 'productivity_model.pkl')
        if os.path.exists(model_path):
            model_data = joblib.load(model_path)
            self.weekly_model = model_data['model']
            self.scaler = model_data['scaler']
            self.is_trained = True

# Sample training data generator
def generate_sample_data(num_samples=1000):
    """Generate sample data for model training"""
    np.random.seed(42)
    
    data = []
    for i in range(num_samples):
        hours_worked = np.random.normal(7.5, 1.5)
        focus_ratio = np.random.beta(5, 2)  # Skewed towards higher focus
        task_completion = np.random.beta(3, 1.5)
        
        # Calculate productivity score (simplified)
        productivity_score = (
            task_completion * 100 * 0.35 +
            focus_ratio * 100 * 0.25 +
            np.random.normal(75, 10) * 0.4
        )
        
        data.append({
            'avg_work_hours': hours_worked,
            'avg_focus_ratio': focus_ratio,
            'task_completion_rate': task_completion,
            'consistency_index': np.random.normal(80, 15),
            'productivity_trend': np.random.normal(0, 5),
            'last_week_momentum': np.random.normal(0, 10),
            'volatility': np.random.normal(10, 3),
            'meeting_load': np.random.beta(2, 5),  # Skewed towards lower meeting load
            'collaboration_intensity': np.random.normal(0.6, 0.2),
            'productivity_score': max(0, min(100, productivity_score))
        })
    
    return pd.DataFrame(data)