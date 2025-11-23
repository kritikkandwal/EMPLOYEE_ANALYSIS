from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from .database import db


import json

# db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='employee')  # 'admin' or 'employee'
    department = db.Column(db.String(64))
    position = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    productivity_logs = db.relationship('ProductivityLog', backref='user', lazy='dynamic')
    badges = db.relationship('Badge', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_recent_productivity(self, days=7):
        return self.productivity_logs.filter(
            ProductivityLog.date >= datetime.utcnow().date().replace(day=datetime.utcnow().day-days)
        ).all()
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'department': self.department,
            'position': self.position
        }

class ProductivityLog(db.Model):
    __tablename__ = 'productivity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    
    # Core metrics
    hours_worked = db.Column(db.Float, default=0.0)
    tasks_completed = db.Column(db.Integer, default=0)
    tasks_assigned = db.Column(db.Integer, default=0)
    focus_time = db.Column(db.Float, default=0.0)  # in hours
    idle_time = db.Column(db.Float, default=0.0)   # in hours
    break_time = db.Column(db.Float, default=0.0)  # in hours
    
    # Calculated metrics
    productivity_score = db.Column(db.Float)  # 0-100
    focus_ratio = db.Column(db.Float)         # 0-1
    task_efficiency = db.Column(db.Float)     # 0-100
    
    # Additional features
    meeting_hours = db.Column(db.Float, default=0.0)
    collaboration_score = db.Column(db.Float, default=0.0)
    mood_score = db.Column(db.Float)  # Optional: from emotion detection
    
    def calculate_metrics(self):
        """Calculate derived metrics"""
        if self.tasks_assigned > 0:
            self.task_efficiency = (self.tasks_completed / self.tasks_assigned) * 100
        
        if self.hours_worked > 0:
            self.focus_ratio = (self.focus_time / self.hours_worked)
            
        # Simplified productivity score calculation
        self.productivity_score = self._calculate_productivity_score()
    
    def _calculate_productivity_score(self):
        """Calculate productivity score using weighted formula"""
        weights = {
            'task_efficiency': 0.35,
            'focus_ratio': 0.25,
            'consistency': 0.15,
            'collaboration': 0.15,
            'attendance': 0.10
        }
        
        score = (
            (self.task_efficiency or 0) * weights['task_efficiency'] +
            (self.focus_ratio or 0) * 100 * weights['focus_ratio'] +
            (self.collaboration_score or 0) * weights['collaboration'] +
            100 * weights['attendance']  # Simplified attendance
        )
        
        return min(100, max(0, score))

class Badge(db.Model):
    __tablename__ = 'badges'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    badge_type = db.Column(db.String(50), nullable=False)
    badge_name = db.Column(db.String(100), nullable=False)
    badge_description = db.Column(db.Text)
    awarded_at = db.Column(db.DateTime, default=datetime.utcnow)
    badge_level = db.Column(db.String(20), default='bronze')  # bronze, silver, gold
    
    def to_dict(self):
        return {
            'type': self.badge_type,
            'name': self.badge_name,
            'description': self.badge_description,
            'awarded_at': self.awarded_at.isoformat(),
            'level': self.badge_level
        }