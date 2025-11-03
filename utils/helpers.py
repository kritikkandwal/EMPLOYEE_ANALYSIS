"""
Helper functions for the AI Productivity Intelligence system
"""
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Format a decimal as a percentage string
    """
    try:
        return f"{value:.{decimals}f}%"
    except (TypeError, ValueError):
        return "0%"

def calculate_trend(current: float, previous: float) -> Dict[str, Any]:
    """
    Calculate trend between current and previous values
    """
    try:
        if previous == 0:
            return {
                'direction': 'stable',
                'percentage': 0,
                'value': 0
            }
        
        change = current - previous
        percentage = (change / abs(previous)) * 100
        
        if percentage > 5:
            direction = 'up'
        elif percentage < -5:
            direction = 'down'
        else:
            direction = 'stable'
        
        return {
            'direction': direction,
            'percentage': abs(percentage),
            'value': change
        }
        
    except Exception as e:
        logger.error(f"Trend calculation error: {e}")
        return {
            'direction': 'stable',
            'percentage': 0,
            'value': 0
        }

def generate_ai_message(score: float, trend: Dict[str, Any], metrics: Dict[str, Any]) -> str:
    """
    Generate AI-powered motivational message based on performance
    """
    try:
        # Base messages for different score ranges
        if score >= 90:
            base_messages = [
                "Outstanding performance! You're at the top of your game.",
                "Exceptional work! Your productivity is inspiring.",
                "Master level achieved! Keep this incredible momentum."
            ]
        elif score >= 80:
            base_messages = [
                "Great job! You're performing at an excellent level.",
                "Strong performance! You're consistently productive.",
                "Well done! Your work habits are very effective."
            ]
        elif score >= 70:
            base_messages = [
                "Good work! You're maintaining solid productivity.",
                "Steady performance! Small improvements can make a big difference.",
                "You're on the right track! Keep optimizing your workflow."
            ]
        elif score >= 60:
            base_messages = [
                "Decent performance! There's room for improvement.",
                "You're making progress! Focus on consistency.",
                "Good foundation! Let's work on boosting your efficiency."
            ]
        else:
            base_messages = [
                "Let's improve together! Every small step counts.",
                "Time for optimization! We'll help you get back on track.",
                "Fresh start opportunity! Let's build better habits."
            ]
        
        # Trend-based modifications
        if trend['direction'] == 'up' and trend['percentage'] > 10:
            modifiers = [
                " And you're improving rapidly!",
                " The upward trend is impressive!",
                " Your progress is accelerating!"
            ]
        elif trend['direction'] == 'up':
            modifiers = [
                " Nice improvement!",
                " Moving in the right direction!",
                " Progress is visible!"
            ]
        elif trend['direction'] == 'down':
            modifiers = [
                " Let's reverse this trend.",
                " We can work on getting back up.",
                " Temporary setback - you've got this!"
            ]
        else:
            modifiers = [
                " Consistency is key!",
                " Steady as she goes!",
                " Maintaining your level!"
            ]
        
        # Metric-specific insights
        insights = []
        
        focus_ratio = metrics.get('focus_ratio', 0)
        if focus_ratio < 0.6:
            insights.append("Try minimizing distractions to improve focus.")
        elif focus_ratio > 0.85:
            insights.append("Your focus levels are excellent!")
        
        task_efficiency = metrics.get('task_efficiency', 0)
        if task_efficiency < 70:
            insights.append("Consider breaking down complex tasks.")
        elif task_efficiency > 95:
            insights.append("Your task completion rate is outstanding!")
        
        # Construct final message
        base_message = random.choice(base_messages)
        modifier = random.choice(modifiers)
        insight = random.choice(insights) if insights else "Keep up the good work!"
        
        return f"{base_message}{modifier} {insight}"
        
    except Exception as e:
        logger.error(f"AI message generation error: {e}")
        return "Keep tracking your productivity for personalized insights!"

def calculate_streak(dates: List[datetime], threshold: float = 70) -> int:
    """
    Calculate consecutive days meeting productivity threshold
    """
    try:
        if not dates:
            return 0
        
        # Sort dates and check consecutiveness
        sorted_dates = sorted(dates)
        streak = 1
        current_streak = 1
        
        for i in range(1, len(sorted_dates)):
            days_diff = (sorted_dates[i] - sorted_dates[i-1]).days
            if days_diff == 1:
                current_streak += 1
                streak = max(streak, current_streak)
            else:
                current_streak = 1
        
        return streak
        
    except Exception as e:
        logger.error(f"Streak calculation error: {e}")
        return 0

def generate_productivity_tips(metrics: Dict[str, Any]) -> List[str]:
    """
    Generate personalized productivity tips based on metrics
    """
    tips = []
    
    # Focus-related tips
    focus_ratio = metrics.get('focus_ratio', 0)
    if focus_ratio < 0.6:
        tips.extend([
            "Use the Pomodoro technique: 25 minutes focused work, 5 minutes break",
            "Turn off notifications during deep work sessions",
            "Create a dedicated workspace free from distractions"
        ])
    
    # Time management tips
    hours_worked = metrics.get('hours_worked', 0)
    if hours_worked > 9:
        tips.extend([
            "Take regular breaks to prevent burnout - try the 52-17 rule",
            "Schedule your most important tasks during your peak energy hours",
            "Use time blocking to structure your day effectively"
        ])
    
    # Task efficiency tips
    task_efficiency = metrics.get('task_efficiency', 0)
    if task_efficiency < 70:
        tips.extend([
            "Break large tasks into smaller, manageable chunks",
            "Use the Eisenhower Matrix to prioritize tasks",
            "Set clear goals for each work session"
        ])
    
    # General productivity tips
    general_tips = [
        "Start your day with your most important task (MIT)",
        "Review your goals and progress at the end of each day",
        "Use the 2-minute rule: if it takes less than 2 minutes, do it now",
        "Batch similar tasks together to maintain focus",
        "Practice single-tasking instead of multitasking"
    ]
    
    # Add general tips if we don't have enough personalized ones
    if len(tips) < 3:
        tips.extend(random.sample(general_tips, 3 - len(tips)))
    
    return tips[:3]  # Return top 3 tips

def safe_divide(numerator: float, denominator: float, default: float = 0) -> float:
    """
    Safely divide two numbers, handling division by zero
    """
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (TypeError, ZeroDivisionError):
        return default

def format_duration(minutes: int) -> str:
    """
    Format duration in minutes to human-readable string
    """
    try:
        if minutes < 60:
            return f"{minutes}m"
        
        hours = minutes // 60
        mins = minutes % 60
        
        if mins == 0:
            return f"{hours}h"
        else:
            return f"{hours}h {mins}m"
    except (TypeError, ValueError):
        return "0m"

def validate_email(email: str) -> bool:
    """
    Validate email format
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def generate_random_color() -> str:
    """
    Generate a random color for charts and UI elements
    """
    colors = [
        '#00ffff', '#00ff88', '#ff64ff', '#ffaa00',
        '#64c8ff', '#8844ff', '#ff4444', '#ffff00'
    ]
    return random.choice(colors)

def calculate_confidence_interval(data: List[float], confidence: float = 0.95) -> tuple:
    """
    Calculate confidence interval for a dataset
    """
    try:
        import numpy as np
        from scipy import stats
        
        if len(data) < 2:
            return (data[0] if data else 0, data[0] if data else 0)
        
        data_array = np.array(data)
        mean = np.mean(data_array)
        sem = stats.sem(data_array)
        margin = sem * stats.t.ppf((1 + confidence) / 2, len(data_array) - 1)
        
        return (mean - margin, mean + margin)
        
    except Exception as e:
        logger.error(f"Confidence interval calculation error: {e}")
        if data:
            return (min(data), max(data))
        return (0, 0)

def parse_date_range(date_range: str) -> tuple:
    """
    Parse date range string to start and end dates
    """
    try:
        today = datetime.now().date()
        
        if date_range == 'week':
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
        elif date_range == 'month':
            start_date = today.replace(day=1)
            next_month = today.replace(day=28) + timedelta(days=4)
            end_date = next_month - timedelta(days=next_month.day)
        elif date_range == 'quarter':
            quarter = (today.month - 1) // 3
            start_date = datetime(today.year, 3 * quarter + 1, 1).date()
            end_date = (start_date + timedelta(days=89)).replace(day=1) - timedelta(days=1)
        else:  # 'all' or invalid
            start_date = today - timedelta(days=365)
            end_date = today
        
        return start_date, end_date
        
    except Exception as e:
        logger.error(f"Date range parsing error: {e}")
        return today - timedelta(days=30), today