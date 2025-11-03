from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from models.user import ProductivityLog, Badge
from datetime import datetime, timedelta
import json

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/attendance')
@login_required
def attendance():
    return render_template('attendance.html')

@analytics_bp.route('/leaderboard')
@login_required
def leaderboard():
    return render_template('leaderboard.html')

@analytics_bp.route('/api/attendance-data')
@login_required
def attendance_data():
    """API endpoint for attendance calendar data"""
    try:
        # Get date range from request
        days = int(request.args.get('days', 30))
        
        # Calculate date range
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        # Get productivity logs for the date range
        logs = ProductivityLog.query.filter(
            ProductivityLog.user_id == current_user.id,
            ProductivityLog.date >= start_date,
            ProductivityLog.date <= end_date
        ).all()
        
        # Format data for calendar
        calendar_data = []
        for log in logs:
            calendar_data.append({
                'date': log.date.isoformat(),
                'productivity_score': log.productivity_score,
                'hours_worked': log.hours_worked,
                'tasks_completed': log.tasks_completed,
                'focus_ratio': log.focus_ratio
            })
        
        # Calculate statistics
        stats = calculate_attendance_stats(logs, days)
        
        return jsonify({
            'calendar_data': calendar_data,
            'stats': stats,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/leaderboard-data')
@login_required
def leaderboard_data():
    """API endpoint for leaderboard data"""
    try:
        timeframe = request.args.get('timeframe', 'monthly')
        department = request.args.get('department', 'all')
        
        # Calculate date range based on timeframe
        if timeframe == 'weekly':
            start_date = datetime.utcnow().date() - timedelta(days=7)
        elif timeframe == 'monthly':
            start_date = datetime.utcnow().date().replace(day=1)
        else:  # quarterly
            start_date = datetime.utcnow().date() - timedelta(days=90)
        
        # Get leaderboard data (simplified implementation)
        leaderboard_data = generate_sample_leaderboard_data(timeframe, department)
        
        # Get user's current rank
        user_rank = calculate_user_rank(current_user.id, leaderboard_data)
        
        return jsonify({
            'leaderboard': leaderboard_data,
            'user_rank': user_rank,
            'timeframe': timeframe,
            'department': department
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def calculate_attendance_stats(logs, days):
    """Calculate attendance statistics"""
    if not logs:
        return {
            'current_streak': 0,
            'attendance_rate': 0,
            'avg_productivity': 0,
            'total_days': 0
        }
    
    # Calculate current streak
    current_streak = calculate_current_streak(logs)
    
    # Calculate attendance rate
    attendance_rate = (len(logs) / days) * 100
    
    # Calculate average productivity
    avg_productivity = sum(log.productivity_score for log in logs) / len(logs)
    
    return {
        'current_streak': current_streak,
        'attendance_rate': round(attendance_rate, 1),
        'avg_productivity': round(avg_productivity, 1),
        'total_days': len(logs)
    }

def calculate_current_streak(logs):
    """Calculate current consecutive days streak"""
    if not logs:
        return 0
    
    # Sort logs by date
    sorted_logs = sorted(logs, key=lambda x: x.date, reverse=True)
    
    streak = 0
    current_date = datetime.utcnow().date()
    
    for log in sorted_logs:
        if log.date == current_date - timedelta(days=streak):
            streak += 1
        else:
            break
    
    return streak

def generate_sample_leaderboard_data(timeframe, department):
    """Generate sample leaderboard data (replace with real data)"""
    sample_users = [
        {'id': 1, 'name': 'Alex Rodriguez', 'department': 'Design', 'score': 92.3, 'badges': 3},
        {'id': 2, 'name': 'Sarah Chen', 'department': 'Engineering', 'score': 88.5, 'badges': 2},
        {'id': 3, 'name': 'Mike Johnson', 'department': 'Marketing', 'score': 85.7, 'badges': 2},
        {'id': 4, 'name': 'Emma Wilson', 'department': 'Sales', 'score': 84.2, 'badges': 1},
        {'id': 5, 'name': 'David Brown', 'department': 'Engineering', 'score': 83.8, 'badges': 2},
        {'id': 6, 'name': 'Lisa Garcia', 'department': 'Design', 'score': 82.9, 'badges': 1},
        {'id': 7, 'name': 'James Miller', 'department': 'Marketing', 'score': 81.5, 'badges': 1},
        {'id': 8, 'name': current_user.username, 'department': current_user.department, 'score': 82.1, 'badges': 1},
        {'id': 9, 'name': 'Anna Davis', 'department': 'Sales', 'score': 79.8, 'badges': 0},
        {'id': 10, 'name': 'Robert Wilson', 'department': 'Engineering', 'score': 78.4, 'badges': 1}
    ]
    
    # Filter by department if specified
    if department != 'all':
        sample_users = [user for user in sample_users if user['department'] == department]
    
    # Sort by score
    sample_users.sort(key=lambda x: x['score'], reverse=True)
    
    # Add ranks
    for i, user in enumerate(sample_users):
        user['rank'] = i + 1
        user['trend'] = 'up' if i % 2 == 0 else 'down'
    
    return sample_users

def calculate_user_rank(user_id, leaderboard_data):
    """Calculate user's rank in leaderboard"""
    for user in leaderboard_data:
        if user['id'] == user_id:
            return {
                'rank': user['rank'],
                'score': user['score'],
                'badges': user['badges'],
                'trend': user['trend']
            }
    
    return {'rank': 0, 'score': 0, 'badges': 0, 'trend': 'stable'}