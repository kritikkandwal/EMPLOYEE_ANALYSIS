from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from models.user import User, ProductivityLog, Badge
# from ml_models.productivity_predictor import ProductivityPredictor
from ml_models.badge_recommender import BadgeRecommender
from datetime import datetime, timedelta
from extensions import db
import json
# from routes.dashboard import dashboard_bp
# app.register_blueprint(dashboard_bp)

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    # Get recent productivity data
    recent_logs = current_user.get_recent_productivity(7)
    
    # Calculate current metrics
    current_metrics = calculate_current_metrics(recent_logs)
    
    # Get AI insights
    ai_insights = generate_ai_insights(current_user, recent_logs)
    
    # Get recommended badges
    badge_recommender = BadgeRecommender()
    all_logs = current_user.productivity_logs.order_by(ProductivityLog.date.desc()).limit(30).all()
    recommended_badges = badge_recommender.recommend_badges(current_user, all_logs)
    
    return render_template('dashboard.html',
                         metrics=current_metrics,
                         insights=ai_insights,
                         badges=recommended_badges)

# @dashboard_bp.route('/api/dashboard-data')
# @login_required
# def dashboard_data():
#     """API endpoint for dashboard data"""
#     days = int(request.args.get('days', 7))
    
#     # Get productivity data
#     logs = current_user.get_recent_productivity(days)
    
#     # Prepare chart data
#     dates = [log.date.strftime('%Y-%m-%d') for log in logs]
#     scores = [log.productivity_score for log in logs]
#     focus_ratios = [log.focus_ratio * 100 for log in logs]
    
#     # Predict next week's productivity
#     predictor = ProductivityPredictor()
#     prediction = predictor.predict_next_week(current_user, logs)
    
#     return jsonify({
#         'dates': dates,
#         'productivity_scores': scores,
#         'focus_ratios': focus_ratios,
#         'prediction': prediction,
#         'current_score': scores[-1] if scores else 75
#     })

@dashboard_bp.route('/api/dashboard-data')
@login_required
def dashboard_data():
    """Temporary mock data for testing charts"""
    days = int(request.args.get('days', 7))

    from datetime import datetime, timedelta
    today = datetime.today()

    dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days)][::-1]
    scores = [65 + i * 2 for i in range(days)]  # Example increasing productivity
    focus_ratios = [70 + (i % 3) * 5 for i in range(days)]

    return jsonify({
        'dates': dates,
        'productivity_scores': scores,
        'focus_ratios': focus_ratios,
        'prediction': 88,
        'current_score': scores[-1]
    })


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