# Routes package initialization
from .auth import auth_bp
from .dashboard import dashboard_bp
from .analytics import analytics_bp
from .admin import admin_bp
from .api import api_bp

__all__ = ['auth_bp', 'dashboard_bp', 'analytics_bp', 'admin_bp', 'api_bp']