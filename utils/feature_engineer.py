import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

class FeatureEngineer:
    """
    Feature engineering for productivity prediction models
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.feature_names = []
    
    def create_temporal_features(self, data: pd.DataFrame, date_column: str = 'date') -> pd.DataFrame:
        """
        Create temporal features from date column
        """
        try:
            data = data.copy()
            data[date_column] = pd.to_datetime(data[date_column])
            
            # Basic temporal features
            data['day_of_week'] = data[date_column].dt.dayofweek
            data['day_of_month'] = data[date_column].dt.day
            data['week_of_year'] = data[date_column].dt.isocalendar().week
            data['month'] = data[date_column].dt.month
            data['quarter'] = data[date_column].dt.quarter
            data['is_weekend'] = data[date_column].dt.dayofweek.isin([5, 6]).astype(int)
            
            # Cyclical features for seasonality
            data['day_sin'] = np.sin(2 * np.pi * data['day_of_week'] / 7)
            data['day_cos'] = np.cos(2 * np.pi * data['day_of_week'] / 7)
            data['month_sin'] = np.sin(2 * np.pi * data['month'] / 12)
            data['month_cos'] = np.cos(2 * np.pi * data['month'] / 12)
            
            logger.info("Temporal features created successfully")
            return data
            
        except Exception as e:
            logger.error(f"Temporal feature creation error: {e}")
            return data
    
    def create_aggregate_features(self, data: pd.DataFrame, user_id: str = 'user_id') -> pd.DataFrame:
        """
        Create aggregate features for user behavior
        """
        try:
            data = data.copy()
            
            # Sort by date for rolling calculations
            data = data.sort_values(['user_id', 'date'])
            
            # User-level aggregates
            user_aggregates = data.groupby('user_id').agg({
                'productivity_score': ['mean', 'std', 'min', 'max'],
                'hours_worked': ['mean', 'std'],
                'task_efficiency': ['mean', 'std'],
                'focus_ratio': ['mean', 'std']
            }).reset_index()
            
            # Flatten column names
            user_aggregates.columns = [
                'user_id',
                'user_avg_productivity', 'user_std_productivity', 'user_min_productivity', 'user_max_productivity',
                'user_avg_hours', 'user_std_hours',
                'user_avg_efficiency', 'user_std_efficiency',
                'user_avg_focus', 'user_std_focus'
            ]
            
            # Merge with original data
            data = data.merge(user_aggregates, on='user_id', how='left')
            
            logger.info("Aggregate features created successfully")
            return data
            
        except Exception as e:
            logger.error(f"Aggregate feature creation error: {e}")
            return data
    
    def create_rolling_features(self, data: pd.DataFrame, windows: List[int] = [7, 14, 30]) -> pd.DataFrame:
        """
        Create rolling window features
        """
        try:
            data = data.copy()
            data = data.sort_values(['user_id', 'date'])
            
            for window in windows:
                # Rolling averages
                data[f'rolling_avg_{window}d'] = data.groupby('user_id')['productivity_score'].transform(
                    lambda x: x.rolling(window=window, min_periods=1).mean()
                )
                
                # Rolling standard deviation
                data[f'rolling_std_{window}d'] = data.groupby('user_id')['productivity_score'].transform(
                    lambda x: x.rolling(window=window, min_periods=1).std()
                )
                
                # Rolling trends
                data[f'rolling_trend_{window}d'] = data.groupby('user_id')['productivity_score'].transform(
                    lambda x: self._calculate_rolling_trend(x, window)
                )
            
            logger.info("Rolling features created successfully")
            return data
            
        except Exception as e:
            logger.error(f"Rolling feature creation error: {e}")
            return data
    
    def _calculate_rolling_trend(self, series: pd.Series, window: int) -> pd.Series:
        """Calculate rolling trend using linear regression"""
        try:
            def linear_trend(x):
                if len(x) < 2:
                    return 0
                time = np.arange(len(x))
                slope = np.polyfit(time, x, 1)[0]
                return slope
            
            return series.rolling(window=window, min_periods=2).apply(linear_trend, raw=False)
        except:
            return pd.Series([0] * len(series), index=series.index)
    
    def create_interaction_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create interaction features between different metrics
        """
        try:
            data = data.copy()
            
            # Efficiency per hour
            data['efficiency_per_hour'] = data['task_efficiency'] / data['hours_worked'].replace(0, 1)
            
            # Focus efficiency
            data['focus_efficiency'] = data['task_efficiency'] * data['focus_ratio']
            
            # Consistency score (inverse of standard deviation)
            data['consistency_score'] = 1 / (1 + data['user_std_productivity'])
            
            # Work intensity
            data['work_intensity'] = data['tasks_completed'] / data['hours_worked'].replace(0, 1)
            
            # Productivity volatility
            data['productivity_volatility'] = data['rolling_std_7d'] / data['rolling_avg_7d'].replace(0, 1)
            
            logger.info("Interaction features created successfully")
            return data
            
        except Exception as e:
            logger.error(f"Interaction feature creation error: {e}")
            return data
    
    def create_trend_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create trend-based features
        """
        try:
            data = data.copy()
            data = data.sort_values(['user_id', 'date'])
            
            # Short-term vs long-term trends
            data['trend_momentum'] = data['rolling_avg_7d'] - data['rolling_avg_30d']
            
            # Acceleration (change in trend)
            data['trend_acceleration'] = data.groupby('user_id')['rolling_trend_7d'].diff()
            
            # Peak detection
            data['is_peak'] = (
                (data['productivity_score'] > data['rolling_avg_7d'] + data['rolling_std_7d']) &
                (data['productivity_score'] > 80)
            ).astype(int)
            
            # Trough detection
            data['is_trough'] = (
                (data['productivity_score'] < data['rolling_avg_7d'] - data['rolling_std_7d']) &
                (data['productivity_score'] < 40)
            ).astype(int)
            
            logger.info("Trend features created successfully")
            return data
            
        except Exception as e:
            logger.error(f"Trend feature creation error: {e}")
            return data
    
    def create_behavioral_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create behavioral pattern features
        """
        try:
            data = data.copy()
            
            # Work pattern consistency
            data['pattern_consistency'] = 1 / (1 + data['user_std_hours'])
            
            # Focus consistency
            data['focus_consistency'] = 1 / (1 + data['user_std_focus'])
            
            # Efficiency consistency
            data['efficiency_consistency'] = 1 / (1 + data['user_std_efficiency'])
            
            # Burnout risk indicator
            data['burnout_risk'] = (
                (data['hours_worked'] > data['user_avg_hours'] + data['user_std_hours']) &
                (data['productivity_score'] < data['user_avg_productivity'])
            ).ast(int)
            
            # Recovery indicator
            data['recovery_indicator'] = (
                (data['hours_worked'] < data['user_avg_hours']) &
                (data['productivity_score'] > data['user_avg_productivity'])
            ).ast(int)
            
            logger.info("Behavioral features created successfully")
            return data
            
        except Exception as e:
            logger.error(f"Behavioral feature creation error: {e}")
            return data
    
    def get_feature_list(self) -> List[str]:
        """
        Get list of engineered feature names
        """
        base_features = [
            'day_of_week', 'day_of_month', 'week_of_year', 'month', 'quarter', 'is_weekend',
            'day_sin', 'day_cos', 'month_sin', 'month_cos',
            'user_avg_productivity', 'user_std_productivity', 'user_min_productivity', 'user_max_productivity',
            'user_avg_hours', 'user_std_hours', 'user_avg_efficiency', 'user_std_efficiency',
            'user_avg_focus', 'user_std_focus'
        ]
        
        rolling_features = []
        for window in [7, 14, 30]:
            rolling_features.extend([
                f'rolling_avg_{window}d',
                f'rolling_std_{window}d',
                f'rolling_trend_{window}d'
            ])
        
        interaction_features = [
            'efficiency_per_hour', 'focus_efficiency', 'consistency_score',
            'work_intensity', 'productivity_volatility'
        ]
        
        trend_features = [
            'trend_momentum', 'trend_acceleration', 'is_peak', 'is_trough'
        ]
        
        behavioral_features = [
            'pattern_consistency', 'focus_consistency', 'efficiency_consistency',
            'burnout_risk', 'recovery_indicator'
        ]
        
        all_features = (
            base_features + rolling_features + 
            interaction_features + trend_features + behavioral_features
        )
        
        return [f for f in all_features if f in self.feature_names]
    
    def prepare_features(self, data: pd.DataFrame, target_column: str = 'productivity_score') -> tuple:
        """
        Prepare features for model training
        """
        try:
            # Create all features
            data = self.create_temporal_features(data)
            data = self.create_aggregate_features(data)
            data = self.create_rolling_features(data)
            data = self.create_interaction_features(data)
            data = self.create_trend_features(data)
            data = self.create_behavioral_features(data)
            
            # Get feature columns (exclude non-feature columns)
            exclude_columns = ['user_id', 'date', target_column, 'task_efficiency', 'focus_ratio']
            feature_columns = [col for col in data.columns if col not in exclude_columns and pd.api.types.is_numeric_dtype(data[col])]
            
            # Handle missing values in features
            data[feature_columns] = data[feature_columns].fillna(0)
            
            # Store feature names
            self.feature_names = feature_columns
            
            # Prepare X and y
            X = data[feature_columns]
            y = data[target_column] if target_column in data.columns else None
            
            logger.info(f"Prepared features: {X.shape}")
            return X, y
            
        except Exception as e:
            logger.error(f"Feature preparation error: {e}")
            return pd.DataFrame(), pd.Series()