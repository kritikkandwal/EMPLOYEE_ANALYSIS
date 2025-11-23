from .predict_attendance import predictor
import json
from datetime import datetime

def train_attendance_models():
    """Train all attendance prediction models"""
    try:
        results = predictor.train_all_models()
        
        training_report = {
            'timestamp': datetime.now().isoformat(),
            'models_trained': results,
            'status': 'success' if any(results.values()) else 'partial_success'
        }
        
        return training_report
        
    except Exception as e:
        return {
            'timestamp': datetime.now().isoformat(),
            'error': str(e),
            'status': 'error'
        }