from routes.attendance_api import attendance_api_bp

from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, send_file
from datetime import datetime, timedelta, date
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

import pandas as pd
import os

# -----------------------------------
# FLASK + DATABASE INITIALIZATION
# -----------------------------------

from models.database import db            # <-- FIX: use global DB
from models.user import User              # <-- FIX: use the real User model

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///productivity.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)                           # <-- FIX: initialize DB correctly

login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# -----------------------------------
# CREATE TABLES + ADMIN USER
# -----------------------------------

with app.app_context():
    db.create_all()

    # Admin auto-create
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


# -----------------------------------
# STATIC ROUTES (UNCHANGED)
# -----------------------------------

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

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'error')
            return redirect(url_for('register'))

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


# --------------------------------------------------------
# ----------- NEW ML ATTENDANCE SYSTEM ROUTES ------------
# --------------------------------------------------------

from models.attendance_models.predict_attendance import predictor
from models.attendance_models.train_models import train_attendance_models

app.config['ATTENDANCE_UPLOAD_FOLDER'] = 'data/attendance/'
app.config['ALLOWED_EXTENSIONS'] = {'csv'}
os.makedirs(app.config['ATTENDANCE_UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/predict-attendance')
@login_required
def predict_attendance():
    try:
        predictions = predictor.predict_all()
        return jsonify(predictions)
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/train-attendance-models')
@login_required
def train_attendance_models_route():
    try:
        report = train_attendance_models()
        return jsonify(report)
    except Exception as e:
        return jsonify({'timestamp': datetime.now().isoformat(), 'error': str(e), 'status': 'error'})


@app.route('/attendance-data')
@login_required
def attendance_data():
    return render_template('attendance_data.html')


@app.route('/api/attendance-data', methods=['GET', 'POST'])
@login_required
def handle_attendance_data():
    if request.method == 'GET':
        try:
            df = predictor.load_data()
            return jsonify({
                'data': df.to_dict('records'),
                'total_records': len(df),
                'date_range': {
                    'start': df['date'].min().strftime('%Y-%m-%d'),
                    'end': df['date'].max().strftime('%Y-%m-%d')
                }
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if file and allowed_file(file.filename):
            try:
                filepath = os.path.join(app.config['ATTENDANCE_UPLOAD_FOLDER'], 'attendance.csv')
                file.save(filepath)

                df = pd.read_csv(filepath)
                if not all(col in df.columns for col in ['date', 'attendance']):
                    return jsonify({'error': 'CSV must contain date and attendance columns'}), 400

                return jsonify({'message': 'File uploaded successfully', 'records': len(df)})
            except Exception as e:
                return jsonify({'error': f'Error processing file: {str(e)}'}), 500

        return jsonify({'error': 'Invalid file type'}), 400


@app.route('/download-attendance-data')
@login_required
def download_attendance_data():
    try:
        df = predictor.load_data()
        download_path = os.path.join(app.config['ATTENDANCE_UPLOAD_FOLDER'], 'attendance_export.csv')
        df.to_csv(download_path, index=False)
        return send_file(download_path, as_attachment=True, download_name='attendance_data.csv')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


app.register_blueprint(attendance_api_bp, url_prefix="/api/attendance")


# -----------------------------------
# RUN APP
# -----------------------------------

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
