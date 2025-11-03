"""
Database configuration and initialization
"""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

def init_db(app):
    """Initialize database with the Flask app"""
    db.init_app(app)
    
    with app.app_context():
        # Import all models here to ensure they are registered with SQLAlchemy
        from .user import User, ProductivityLog, Badge
        
        # Create all tables
        db.create_all()
        
        # Create admin user if doesn't exist
        create_initial_data()

def create_initial_data():
    """Create initial database data"""
    from .user import User, db
    
    # Check if admin user exists
    admin = User.query.filter_by(email='admin@productivity.ai').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@productivity.ai',
            role='admin',
            department='IT',
            position='System Administrator'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

def get_db_session():
    """Get database session"""
    return db.session

def close_db_session(exception=None):
    """Close database session"""
    db.session.remove()