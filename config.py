import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///productivity.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # AI Model Configurations
    ML_MODELS_PATH = 'data/trained_models/'
    PRODUCTIVITY_THRESHOLD_HIGH = 80
    PRODUCTIVITY_THRESHOLD_MEDIUM = 40
    
    # Feature weights for MPS calculation
    MPS_WEIGHTS = {
        'task_efficiency': 0.35,
        'focus_ratio': 0.25,
        'on_time_completion': 0.15,
        'consistency': 0.10,
        'collaboration': 0.10,
        'attendance': 0.05
    }
    
    # Badge thresholds
    BADGE_THRESHOLDS = {
        'focus_master': 0.85,
        'consistency_king': 0.80,
        'early_bird': 0.75
    }