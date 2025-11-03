import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class DataProcessor:
    """
    Process and clean productivity data for ML models
    """
    
    def __init__(self):
        self.required_columns = [
            'user_id', 'date', 'hours_worked', 'tasks_completed',
            'tasks_assigned', 'focus_time', 'idle_time'
        ]
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        Validate input data structure and quality
        """
        try:
            # Check required columns
            missing_columns = set(self.required_columns) - set(data.columns)
            if missing_columns:
                logger.warning(f"Missing columns: {missing_columns}")
                return False
            
            # Check data types
            if not pd.api.types.is_numeric_dtype(data['hours_worked']):
                logger.warning("hours_worked must be numeric")
                return False
            
            # Check for negative values
            if (data['hours_worked'] < 0).any():
                logger.warning("Negative values found in hours_worked")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Data validation error: {e}")
            return False
    
    def clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and preprocess productivity data
        """
        try:
            # Create a copy to avoid modifying original data
            cleaned_data = data.copy()
            
            # Handle missing values
            cleaned_data = self._handle_missing_values(cleaned_data)
            
            # Remove outliers
            cleaned_data = self._remove_outliers(cleaned_data)
            
            # Calculate derived metrics
            cleaned_data = self._calculate_derived_metrics(cleaned_data)
            
            # Normalize data
            cleaned_data = self._normalize_data(cleaned_data)
            
            logger.info(f"Cleaned data shape: {cleaned_data.shape}")
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Data cleaning error: {e}")
            return data
    
    def _handle_missing_values(self, data: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values in the dataset"""
        # For numeric columns, fill with median
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            if data[col].isnull().any():
                data[col] = data[col].fillna(data[col].median())
        
        # For date columns, forward fill
        if 'date' in data.columns and data['date'].isnull().any():
            data['date'] = data['date'].fillna(method='ffill')
        
        return data
    
    def _remove_outliers(self, data: pd.DataFrame) -> pd.DataFrame:
        """Remove outliers using IQR method"""
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        
        for col in numeric_columns:
            if col in ['user_id', 'date']:
                continue
                
            Q1 = data[col].quantile(0.25)
            Q3 = data[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # Cap outliers instead of removing
            data[col] = data[col].clip(lower=lower_bound, upper=upper_bound)
        
        return data
    
    def _calculate_derived_metrics(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate derived productivity metrics"""
        # Task efficiency
        data['task_efficiency'] = (data['tasks_completed'] / data['tasks_assigned']).replace([np.inf, -np.inf], 0) * 100
        
        # Focus ratio
        data['focus_ratio'] = (data['focus_time'] / data['hours_worked']).replace([np.inf, -np.inf], 0)
        
        # Productivity score (simplified)
        data['productivity_score'] = self._calculate_productivity_score(data)
        
        return data
    
    def _calculate_productivity_score(self, data: pd.DataFrame) -> pd.Series:
        """Calculate comprehensive productivity score"""
        from .constants import MPS_WEIGHTS
        
        # Normalize components to 0-100 scale
        task_efficiency = data['task_efficiency'].clip(0, 100)
        focus_ratio = (data['focus_ratio'] * 100).clip(0, 100)
        
        # Simplified calculation (in production, use all weights)
        score = (
            task_efficiency * MPS_WEIGHTS['task_efficiency'] +
            focus_ratio * MPS_WEIGHTS['focus_ratio'] +
            80 * MPS_WEIGHTS['consistency'] +  # Placeholder
            75 * MPS_WEIGHTS['collaboration'] +  # Placeholder
            95 * MPS_WEIGHTS['attendance']  # Placeholder
        )
        
        return score.clip(0, 100)
    
    def _normalize_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Normalize data for ML models"""
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        
        # Skip normalization for certain columns
        skip_columns = ['user_id', 'date', 'productivity_score']
        normalize_columns = [col for col in numeric_columns if col not in skip_columns]
        
        for col in normalize_columns:
            if data[col].std() > 0:  # Avoid division by zero
                data[f'{col}_normalized'] = (data[col] - data[col].mean()) / data[col].std()
        
        return data
    
    def aggregate_weekly_data(self, daily_data: pd.DataFrame) -> pd.DataFrame:
        """Aggregate daily data to weekly level"""
        try:
            # Ensure date is datetime
            daily_data['date'] = pd.to_datetime(daily_data['date'])
            
            # Group by week and user
            weekly_data = daily_data.groupby([
                'user_id',
                pd.Grouper(key='date', freq='W-MON')
            ]).agg({
                'hours_worked': 'sum',
                'tasks_completed': 'sum',
                'tasks_assigned': 'sum',
                'focus_time': 'sum',
                'idle_time': 'sum',
                'productivity_score': 'mean',
                'task_efficiency': 'mean',
                'focus_ratio': 'mean'
            }).reset_index()
            
            # Calculate weekly metrics
            weekly_data['week_number'] = weekly_data['date'].dt.isocalendar().week
            weekly_data['year'] = weekly_data['date'].dt.year
            
            logger.info(f"Weekly data shape: {weekly_data.shape}")
            return weekly_data
            
        except Exception as e:
            logger.error(f"Weekly aggregation error: {e}")
            return pd.DataFrame()
    
    def detect_anomalies(self, data: pd.DataFrame, method: str = 'zscore') -> pd.DataFrame:
        """Detect anomalies in productivity data"""
        try:
            if method == 'zscore':
                return self._zscore_anomaly_detection(data)
            elif method == 'iqr':
                return self._iqr_anomaly_detection(data)
            else:
                logger.warning(f"Unknown anomaly detection method: {method}")
                return data
                
        except Exception as e:
            logger.error(f"Anomaly detection error: {e}")
            return data
    
    def _zscore_anomaly_detection(self, data: pd.DataFrame) -> pd.DataFrame:
        """Detect anomalies using Z-score method"""
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        data = data.copy()
        
        for col in numeric_columns:
            if col in ['user_id', 'date']:
                continue
                
            z_scores = np.abs((data[col] - data[col].mean()) / data[col].std())
            data[f'{col}_anomaly'] = z_scores > 3  # 3 standard deviations
        
        return data
    
    def _iqr_anomaly_detection(self, data: pd.DataFrame) -> pd.DataFrame:
        """Detect anomalies using IQR method"""
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        data = data.copy()
        
        for col in numeric_columns:
            if col in ['user_id', 'date']:
                continue
                
            Q1 = data[col].quantile(0.25)
            Q3 = data[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            data[f'{col}_anomaly'] = (data[col] < lower_bound) | (data[col] > upper_bound)
        
        return data