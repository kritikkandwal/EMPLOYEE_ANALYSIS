from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from models.user import User, ProductivityLog, Badge, db
from datetime import datetime, timedelta
import pandas as pd
import json

admin_bp = Blueprint('admin', __name__)

@admin_bp.before_request
@login_required
def check_admin():
    """Check if user is admin before allowing access to admin routes"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

@admin_bp.route('/admin')
@login_required
def admin_dashboard():
    """Admin dashboard page"""
    return render_template('admin.html')

@admin_bp.route('/api/admin/stats')
@login_required
def admin_stats():
    """API endpoint for admin statistics"""
    try:
        # Get basic statistics
        total_users = User.query.count()
        active_users = User.query.filter(User.last_login >= datetime.utcnow() - timedelta(days=30)).count()
        
        # Get productivity statistics
        productivity_logs = ProductivityLog.query.filter(
            ProductivityLog.date >= datetime.utcnow().date() - timedelta(days=30)
        ).all()
        
        if productivity_logs:
            avg_productivity = sum(log.productivity_score for log in productivity_logs) / len(productivity_logs)
            total_tasks = sum(log.tasks_completed for log in productivity_logs)
        else:
            avg_productivity = 0
            total_tasks = 0
        
        # Get department statistics
        departments = db.session.query(
            User.department,
            db.func.count(User.id),
            db.func.avg(ProductivityLog.productivity_score)
        ).join(ProductivityLog).group_by(User.department).all()
        
        department_stats = []
        for dept, user_count, avg_score in departments:
            department_stats.append({
                'department': dept,
                'user_count': user_count,
                'avg_productivity': round(avg_score or 0, 1)
            })
        
        return jsonify({
            'total_users': total_users,
            'active_users': active_users,
            'avg_productivity': round(avg_productivity, 1),
            'total_tasks': total_tasks,
            'department_stats': department_stats
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/admin/users')
@login_required
def admin_users():
    """API endpoint for user management"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Get users with pagination
        users_query = User.query
        total_users = users_query.count()
        
        users = users_query.offset((page - 1) * per_page).limit(per_page).all()
        
        user_data = []
        for user in users:
            # Get user's recent productivity
            recent_log = ProductivityLog.query.filter_by(user_id=user.id)\
                .order_by(ProductivityLog.date.desc()).first()
            
            user_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'department': user.department,
                'position': user.position,
                'role': user.role,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'current_productivity': recent_log.productivity_score if recent_log else 0,
                'status': 'active' if user.last_login and user.last_login >= datetime.utcnow() - timedelta(days=7) else 'inactive'
            })
        
        return jsonify({
            'users': user_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_users,
                'pages': (total_users + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/admin/productivity-trends')
@login_required
def productivity_trends():
    """API endpoint for productivity trends analysis"""
    try:
        days = int(request.args.get('days', 30))
        
        # Get productivity data for the date range
        start_date = datetime.utcnow().date() - timedelta(days=days)
        
        logs = ProductivityLog.query.filter(
            ProductivityLog.date >= start_date
        ).all()
        
        if not logs:
            return jsonify({'trends': [], 'summary': {}})
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame([{
            'date': log.date,
            'user_id': log.user_id,
            'productivity_score': log.productivity_score,
            'hours_worked': log.hours_worked,
            'focus_ratio': log.focus_ratio
        } for log in logs])
        
        # Calculate daily averages
        daily_avg = df.groupby('date').agg({
            'productivity_score': 'mean',
            'hours_worked': 'mean',
            'focus_ratio': 'mean'
        }).reset_index()
        
        trends_data = []
        for _, row in daily_avg.iterrows():
            trends_data.append({
                'date': row['date'].isoformat(),
                'productivity_score': round(row['productivity_score'], 1),
                'hours_worked': round(row['hours_worked'], 1),
                'focus_ratio': round(row['focus_ratio'], 2)
            })
        
        # Calculate summary statistics
        summary = {
            'avg_productivity': round(df['productivity_score'].mean(), 1),
            'avg_hours_worked': round(df['hours_worked'].mean(), 1),
            'avg_focus_ratio': round(df['focus_ratio'].mean(), 2),
            'total_logs': len(logs),
            'unique_users': df['user_id'].nunique()
        }
        
        return jsonify({
            'trends': trends_data,
            'summary': summary
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/admin/system-alerts')
@login_required
def system_alerts():
    """API endpoint for system alerts"""
    try:
        # Sample system alerts (replace with real monitoring)
        alerts = [
            {
                'id': 1,
                'type': 'critical',
                'title': 'High CPU Usage',
                'message': 'Server CPU usage at 92%',
                'timestamp': (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
                'resolved': False
            },
            {
                'id': 2,
                'type': 'warning',
                'title': 'Database Backup Required',
                'message': 'Last backup 6 days ago',
                'timestamp': (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                'resolved': False
            },
            {
                'id': 3,
                'type': 'warning',
                'title': 'Memory Usage High',
                'message': 'Memory usage at 87%',
                'timestamp': (datetime.utcnow() - timedelta(hours=4)).isoformat(),
                'resolved': False
            }
        ]
        
        return jsonify(alerts)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/admin/user/<int:user_id>')
@login_required
def user_detail(user_id):
    """API endpoint for detailed user information"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Get user's productivity history
        logs = ProductivityLog.query.filter_by(user_id=user_id)\
            .order_by(ProductivityLog.date.desc()).limit(30).all()
        
        # Get user's badges
        badges = Badge.query.filter_by(user_id=user_id).all()
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'department': user.department,
            'position': user.position,
            'role': user.role,
            'created_at': user.created_at.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'productivity_history': [{
                'date': log.date.isoformat(),
                'productivity_score': log.productivity_score,
                'hours_worked': log.hours_worked,
                'tasks_completed': log.tasks_completed,
                'focus_ratio': log.focus_ratio
            } for log in logs],
            'badges': [badge.to_dict() for badge in badges]
        }
        
        return jsonify(user_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/admin/update-user/<int:user_id>', methods=['POST'])
@login_required
def update_user(user_id):
    """API endpoint to update user information"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        # Update allowed fields
        allowed_fields = ['department', 'position', 'role']
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'User updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500