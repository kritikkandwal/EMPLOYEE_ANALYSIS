"""
Constants and configuration for the AI Productivity Intelligence system
"""

# Productivity Score Weights
MPS_WEIGHTS = {
    'task_efficiency': 0.35,
    'focus_ratio': 0.25,
    'on_time_completion': 0.15,
    'consistency': 0.10,
    'collaboration': 0.10,
    'attendance': 0.05
}

# Badge Thresholds
BADGE_THRESHOLDS = {
    'focus_master': 0.85,           # Focus ratio threshold
    'consistency_king': 0.80,       # Consistency threshold
    'early_bird': 0.75,             # Morning productivity threshold
    'deadline_crusher': 0.95,       # On-time completion rate
    'improvement_champ': 0.10,      # Minimum improvement percentage
    'marathon_worker': 7,           # Consecutive productive days
    'task_maestro': 50,             # Monthly task completion count
}

# Productivity Levels
PRODUCTIVITY_LEVELS = {
    'high': (80, 100),
    'medium': (40, 79),
    'low': (0, 39)
}

# Time Constants
WORK_HOURS_START = 9
WORK_HOURS_END = 17
PEAK_HOURS_MORNING = (10, 12)
PEAK_HOURS_AFTERNOON = (14, 16)

# AI Model Parameters
MODEL_PARAMS = {
    'productivity_predictor': {
        'n_estimators': 100,
        'max_depth': 10,
        'learning_rate': 0.1
    },
    'badge_recommender': {
        'min_samples': 7,
        'confidence_threshold': 0.8
    }
}

# Feature Names
FEATURE_NAMES = [
    'avg_work_hours',
    'avg_focus_ratio',
    'task_completion_rate',
    'consistency_index',
    'productivity_trend',
    'last_week_momentum',
    'volatility',
    'meeting_load',
    'collaboration_intensity'
]

# Color Schemes
COLORS = {
    'primary': '#00ffff',
    'secondary': '#ff00ff',
    'accent': '#00ff88',
    'success': '#00ff88',
    'warning': '#ffaa00',
    'error': '#ff4444',
    'background': '#0a0a0f'
}

# UI Constants
CHART_COLORS = [
    '#00ffff', '#00ff88', '#ff64ff', '#ffaa00', 
    '#64c8ff', '#ff4444', '#8844ff', '#ffff00'
]

# API Endpoints
API_ENDPOINTS = {
    'productivity_prediction': '/api/predict/productivity',
    'badge_recommendation': '/api/recommend/badges',
    'ai_insights': '/api/generate/insights',
    'user_analytics': '/api/analytics/user'
}

# Database Configuration
DB_CONFIG = {
    'max_connections': 20,
    'stale_timeout': 300
}

# Performance Thresholds
PERFORMANCE_THRESHOLDS = {
    'excellent': 90,
    'good': 75,
    'average': 60,
    'needs_improvement': 40
}

# Notification Settings
NOTIFICATION_SETTINGS = {
    'productivity_alert': 40,
    'streak_alert': 3,
    'goal_achievement': True,
    'weekly_summary': True
}