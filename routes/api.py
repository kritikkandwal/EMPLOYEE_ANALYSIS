from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from models.user import ProductivityLog, User, Badge
from ml_models.productivity_predictor import ProductivityPredictor
from ml_models.badge_recommender import BadgeRecommender
from ml_models.recommendation_engine import RecommendationEngine
from datetime import datetime, timedelta
import json

api_bp = Blueprint('api', __name__)

# Initialize ML models
productivity_predictor = ProductivityPredictor()
badge_recommender = BadgeRecommender()
recommendation_engine = RecommendationEngine()

@api_bp.route('/api/dashboard-data')
@login_required
def dashboard_data():
    """API endpoint for dashboard data"""
    try:
        days = int(request.args.get('days', 7))
        
        # Get recent productivity data
        recent_logs = current_user.get_recent_productivity(days)
        
        # Prepare chart data
        dates = [log.date.strftime('%Y-%m-%d') for log in recent_logs]
        scores = [log.productivity_score for log in recent_logs]
        focus_ratios = [log.focus_ratio * 100 for log in recent_logs]
        
        # Calculate current metrics
        current_metrics = calculate_current_metrics(recent_logs)
        
        # Generate AI insights
        ai_insights = generate_ai_insights(current_user, recent_logs)
        
        # Get badge recommendations
        all_logs = current_user.productivity_logs.order_by(ProductivityLog.date.desc()).limit(30).all()
        recommended_badges = badge_recommender.recommend_badges(current_user, all_logs)
        
        # Predict next week's productivity
        prediction = productivity_predictor.predict_next_week(current_user, recent_logs)
        
        return jsonify({
            'dates': dates,
            'productivity_scores': scores,
            'focus_ratios': focus_ratios,
            'current_metrics': current_metrics,
            'ai_insights': ai_insights,
            'recommended_badges': recommended_badges,
            'prediction': prediction,
            'current_score': scores[-1] if scores else 75
        })
        
    except Exception as e:
        current_app.logger.error(f"Dashboard data error: {e}")
        return jsonify({'error': 'Failed to load dashboard data'}), 500

@api_bp.route('/api/productivity-log', methods=['POST'])
@login_required
def log_productivity():
    """API endpoint to log daily productivity"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['date', 'hours_worked', 'tasks_completed', 'tasks_assigned']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create or update productivity log
        log_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        existing_log = ProductivityLog.query.filter_by(
            user_id=current_user.id,
            date=log_date
        ).first()
        
        if existing_log:
            # Update existing log
            existing_log.hours_worked = data['hours_worked']
            existing_log.tasks_completed = data['tasks_completed']
            existing_log.tasks_assigned = data['tasks_assigned']
            existing_log.focus_time = data.get('focus_time', 0)
            existing_log.idle_time = data.get('idle_time', 0)
            existing_log.break_time = data.get('break_time', 0)
            existing_log.meeting_hours = data.get('meeting_hours', 0)
            existing_log.collaboration_score = data.get('collaboration_score', 0)
            existing_log.mood_score = data.get('mood_score', 0)
        else:
            # Create new log
            existing_log = ProductivityLog(
                user_id=current_user.id,
                date=log_date,
                hours_worked=data['hours_worked'],
                tasks_completed=data['tasks_completed'],
                tasks_assigned=data['tasks_assigned'],
                focus_time=data.get('focus_time', 0),
                idle_time=data.get('idle_time', 0),
                break_time=data.get('break_time', 0),
                meeting_hours=data.get('meeting_hours', 0),
                collaboration_score=data.get('collaboration_score', 0),
                mood_score=data.get('mood_score', 0)
            )
            from models.user import db
            db.session.add(existing_log)
        
        # Calculate metrics
        existing_log.calculate_metrics()
        
        # Save to database
        from models.user import db
        db.session.commit()
        
        # Check for new badges
        new_badges = badge_recommender.recommend_badges(current_user, [existing_log])
        
        return jsonify({
            'success': True,
            'log_id': existing_log.id,
            'productivity_score': existing_log.productivity_score,
            'new_badges': new_badges
        })
        
    except Exception as e:
        current_app.logger.error(f"Productivity log error: {e}")
        return jsonify({'error': 'Failed to log productivity data'}), 500

@api_bp.route('/api/predict/productivity')
@login_required
def predict_productivity():
    """API endpoint for productivity prediction"""
    try:
        days = int(request.args.get('days', 7))
        
        # Get recent data for prediction
        recent_logs = current_user.get_recent_productivity(days)
        
        if not recent_logs:
            return jsonify({'prediction': 75, 'confidence': 0.5})
        
        # Generate prediction
        prediction = productivity_predictor.predict_next_week(current_user, recent_logs)
        
        return jsonify({
            'prediction': prediction,
            'confidence': 0.85,  # Placeholder confidence score
            'trend': 'up' if prediction > (recent_logs[-1].productivity_score if recent_logs else 75) else 'down'
        })
        
    except Exception as e:
        current_app.logger.error(f"Productivity prediction error: {e}")
        return jsonify({'error': 'Failed to generate prediction'}), 500

@api_bp.route('/api/recommendations')
@login_required
def get_recommendations():
    """API endpoint for AI recommendations"""
    try:
        days = int(request.args.get('days', 30))
        
        # Get recent productivity data
        recent_logs = current_user.get_recent_productivity(days)
        
        if not recent_logs:
            return jsonify({'recommendations': []})
        
        # Generate recommendations
        recommendations = recommendation_engine.generate_recommendations(current_user, recent_logs)
        
        return jsonify({
            'recommendations': recommendations,
            'generated_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Recommendations error: {e}")
        return jsonify({'error': 'Failed to generate recommendations'}), 500

@api_bp.route('/api/badges')
@login_required
def get_badges():
    """API endpoint for user badges"""
    try:
        # Get earned badges
        earned_badges = current_user.badges.all()
        
        # Get recommended badges
        recent_logs = current_user.get_recent_productivity(30)
        recommended_badges = badge_recommender.recommend_badges(current_user, recent_logs)
        
        return jsonify({
            'earned_badges': [badge.to_dict() for badge in earned_badges],
            'recommended_badges': recommended_badges
        })
        
    except Exception as e:
        current_app.logger.error(f"Badges error: {e}")
        return jsonify({'error': 'Failed to load badges'}), 500

@api_bp.route('/api/user/profile')
@login_required
def user_profile():
    """API endpoint for user profile data"""
    try:
        return jsonify(current_user.to_dict())
        
    except Exception as e:
        current_app.logger.error(f"User profile error: {e}")
        return jsonify({'error': 'Failed to load user profile'}), 500

@api_bp.route('/api/notifications')
@login_required
def get_notifications():
    """API endpoint for user notifications"""
    try:
        # Sample notifications (replace with real implementation)
        notifications = [
            {
                'id': 1,
                'type': 'info',
                'message': 'Your productivity has improved by 5% this week!',
                'time': '2 hours ago',
                'read': False
            },
            {
                'id': 2,
                'type': 'success',
                'message': 'You earned the Focus Master badge!',
                'time': '1 day ago',
                'read': True
            },
            {
                'id': 3,
                'type': 'warning',
                'message': 'Low focus time detected yesterday',
                'time': '2 days ago',
                'read': True
            }
        ]
        
        return jsonify(notifications)
        
    except Exception as e:
        current_app.logger.error(f"Notifications error: {e}")
        return jsonify({'error': 'Failed to load notifications'}), 500

# Helper functions
def calculate_current_metrics(logs):
    """Calculate current productivity metrics"""
    if not logs:
        return {
            'productivity_score': 75,
            'focus_ratio': 0.7,
            'task_efficiency': 80,
            'weekly_trend': 0
        }
    
    recent_scores = [log.productivity_score for log in logs]
    avg_score = sum(recent_scores) / len(recent_scores)
    avg_focus = sum(log.focus_ratio for log in logs) / len(logs)
    avg_efficiency = sum(log.task_efficiency for log in logs) / len(logs)
    
    # Calculate trend
    if len(recent_scores) > 1:
        trend = recent_scores[-1] - recent_scores[0]
    else:
        trend = 0
    
    return {
        'productivity_score': round(avg_score, 1),
        'focus_ratio': round(avg_focus, 2),
        'task_efficiency': round(avg_efficiency, 1),
        'weekly_trend': round(trend, 1)
    }

def generate_ai_insights(user, logs):
    """Generate AI-powered insights"""
    if not logs:
        return {
            'today_insight': "Start tracking your productivity to get personalized insights!",
            'tomorrow_prediction': "Complete your first task to get predictions.",
            'recommendation': "Set up your work schedule to begin analysis."
        }
    
    recent_score = logs[0].productivity_score if logs else 75
    avg_focus = sum(log.focus_ratio for log in logs) / len(logs) if logs else 0.7
    
    insights = []
    
    # Generate insights based on data
    if recent_score >= 80:
        insights.append("Excellent productivity today! Keep up the great work.")
    elif recent_score >= 60:
        insights.append("Good performance. Small improvements can boost your score further.")
    else:
        insights.append("Consider optimizing your work routine for better productivity.")
    
    if avg_focus < 0.6:
        insights.append("Your focus ratio is lower than optimal. Try minimizing distractions.")
    
    # Time-based insights
    current_hour = datetime.now().hour
    if 10 <= current_hour <= 12:
        insights.append("You're in your peak productivity window. Tackle important tasks now!")
    
    return {
        'today_insight': insights[0] if insights else "Keep tracking for personalized insights!",
        'tomorrow_prediction': f"Predicted score: {min(95, recent_score + 5)} based on your trend",
        'recommendation': "Try the Pomodoro technique for better focus." if avg_focus < 0.7 else "Maintain your current focus routine."
    }