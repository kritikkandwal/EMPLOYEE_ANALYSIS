"""
Data management for ML model training and storage
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Any
import os

logger = logging.getLogger(__name__)

class ProductivityDataManager:
    """
    Manage productivity data for ML model training and storage
    """
    
    def __init__(self, data_path='data/'):
        self.data_path = data_path
        self.training_data_file = os.path.join(data_path, 'training_data.csv')
        self.model_performance_file = os.path.join(data_path, 'model_performance.json')
        
        # Create data directory
        os.makedirs(data_path, exist_ok=True)
    
    def load_training_data(self) -> pd.DataFrame:
        """Load training data from file"""
        try:
            if os.path.exists(self.training_data_file):
                df = pd.read_csv(self.training_data_file)
                logger.info(f"Loaded training data: {df.shape}")
                return df
            else:
                logger.info("No training data found, generating sample data")
                return self.generate_initial_data()
        except Exception as e:
            logger.error(f"Error loading training data: {e}")
            return self.generate_initial_data()
    
    def save_training_data(self, data: pd.DataFrame):
        """Save training data to file"""
        try:
            data.to_csv(self.training_data_file, index=False)
            logger.info(f"Saved training data: {data.shape}")
        except Exception as e:
            logger.error(f"Error saving training data: {e}")
    
    def generate_initial_data(self, num_samples: int = 5000) -> pd.DataFrame:
        """Generate initial training data"""
        from ml_models.advanced_predictor import generate_advanced_sample_data
        data = generate_advanced_sample_data(num_samples)
        self.save_training_data(data)
        return data
    
    def add_user_data(self, user_data: Dict[str, Any]):
        """Add new user data to training set"""
        try:
            # Load existing data
            existing_data = self.load_training_data()
            
            # Convert user data to DataFrame
            new_data = pd.DataFrame([user_data])
            
            # Combine and save
            updated_data = pd.concat([existing_data, new_data], ignore_index=True)
            self.save_training_data(updated_data)
            
            logger.info(f"Added new user data, total samples: {len(updated_data)}")
            
        except Exception as e:
            logger.error(f"Error adding user data: {e}")
    
    def get_model_performance(self) -> Dict[str, Any]:
        """Load model performance history"""
        try:
            if os.path.exists(self.model_performance_file):
                with open(self.model_performance_file, 'r') as f:
                    return json.load(f)
            else:
                return {'models': {}, 'best_model': None}
        except Exception as e:
            logger.error(f"Error loading model performance: {e}")
            return {'models': {}, 'best_model': None}
    
    def save_model_performance(self, model_name: str, performance: Dict[str, Any]):
        """Save model performance metrics"""
        try:
            performance_data = self.get_model_performance()
            performance_data['models'][model_name] = {
                **performance,
                'timestamp': datetime.now().isoformat()
            }
            
            # Update best model if needed
            current_best = performance_data.get('best_model')
            if (not current_best or 
                performance['mae'] < performance_data['models'][current_best]['mae']):
                performance_data['best_model'] = model_name
            
            with open(self.model_performance_file, 'w') as f:
                json.dump(performance_data, f, indent=2)
                
            logger.info(f"Saved performance for {model_name}: MAE={performance['mae']:.2f}")
            
        except Exception as e:
            logger.error(f"Error saving model performance: {e}")
    
    def get_data_statistics(self) -> Dict[str, Any]:
        """Get statistics about the training data"""
        try:
            data = self.load_training_data()
            
            stats = {
                'total_samples': len(data),
                'features': list(data.columns),
                'numeric_stats': {},
                'data_quality': {}
            }
            
            # Numeric statistics
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                stats['numeric_stats'][col] = {
                    'mean': data[col].mean(),
                    'std': data[col].std(),
                    'min': data[col].min(),
                    'max': data[col].max()
                }
            
            # Data quality
            stats['data_quality'] = {
                'missing_values': data.isnull().sum().to_dict(),
                'duplicates': data.duplicated().sum(),
                'memory_usage_mb': data.memory_usage(deep=True).sum() / 1024**2
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating data statistics: {e}")
            return {}