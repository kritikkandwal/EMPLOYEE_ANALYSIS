from flask import Flask, render_template, redirect, url_for, flash, request, jsonify

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///productivity.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Single SQLAlchemy instance
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    department = db.Column(db.String(64), default='General')
    position = db.Column(db.String(64), default='Employee')
    role = db.Column(db.String(20), default='employee')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create tables
with app.app_context():
    db.create_all()
    
    # Create admin user if doesn't exist
    if not User.query.filter_by(email='admin@productivity.ai').first():
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
        print("✓ Created admin user")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()

            # Check if request is AJAX (JS fetch)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"success": True, "redirect": url_for('dashboard')})
            else:
                flash('Logged in successfully!', 'success')
                return redirect(url_for('dashboard'))
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"success": False, "error": "Invalid email or password"}), 401
            else:
                flash('Invalid email or password', 'error')
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        department = request.form.get('department', 'General')
        position = request.form.get('position', 'Employee')
        
        # Check if user exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'error')
            return redirect(url_for('register'))
        
        # Create new user
        user = User(
            username=username, 
            email=email,
            department=department,
            position=position
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    metrics = {
        "productivity_score": 85,
        "focus_ratio": 0.76,
        "task_efficiency": 90,
        "weekly_trend": 5
    }

    insights = {
        "today_insight": "You were 15% more productive today than yesterday.",
        "tomorrow_prediction": "Expected 10% improvement if you keep focus above 80%.",
        "recommendation": "Try focusing on one task at a time for better efficiency."
    }

    badges = [
        {"name": "Consistency Champ", "description": "Logged in 7 days in a row.", "level": "gold"},
        {"name": "Task Master", "description": "Completed 50+ tasks efficiently.", "level": "silver"}
    ]

    return render_template('dashboard.html', metrics=metrics, insights=insights, badges=badges)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/attendance')
@login_required
def attendance():
    return render_template('attendance.html')

@app.route('/leaderboard')
@login_required
def leaderboard():
    return render_template('leaderboard.html')

@app.route('/productivity-trends')
@login_required
def productivity_trends():
    return render_template('productivity_trends.html')

@app.route('/task-analysis')
@login_required
def task_analysis():
    return render_template('task_analysis.html')

@app.route('/time-tracking')
@login_required
def time_tracking():
    return render_template('time_tracking.html')




if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)