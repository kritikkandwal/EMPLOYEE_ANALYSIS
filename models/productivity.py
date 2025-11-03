"""
Productivity models and calculations
"""
from .user import db
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np
from sqlalchemy import func

class ProductivityAnalyzer:
    """
    Analyze productivity patterns and trends
    """
    
    def __init__(self, user_id: int):
        self.user_id = user_id
    
    def get_weekly_summary(self, weeks: int = 4) -> Dict:
        """
        Get weekly productivity summary
        """
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(weeks=weeks)
        
        logs = self._get_logs_in_range(start_date, end_date)
        
        if not logs:
            return self._empty_weekly_summary(weeks)
        
        # Group by week
        weekly_data = {}
        for log in logs:
            week_start = log.date - timedelta(days=log.date.weekday())
            week_key = week_start.isoformat()
            
            if week_key not in weekly_data:
                weekly_data[week_key] = {
                    'week_start': week_start,
                    'logs': [],
                    'total_hours': 0,
                    'total_tasks': 0,
                    'scores': []
                }
            
            weekly_data[week_key]['logs'].append(log)
            weekly_data[week_key]['total_hours'] += log.hours_worked
            weekly_data[week_key]['total_tasks'] += log.tasks_completed
            weekly_data[week_key]['scores'].append(log.productivity_score)
        
        # Calculate weekly metrics
        summary = []
        for week_key, data in weekly_data.items():
            avg_score = np.mean(data['scores']) if data['scores'] else 0
            avg_focus = np.mean([log.focus_ratio for log in data['logs']]) if data['logs'] else 0
            
            summary.append({
                'week_start': data['week_start'].isoformat(),
                'avg_productivity': round(avg_score, 1),
                'avg_focus_ratio': round(avg_focus, 2),
                'total_hours': round(data['total_hours'], 1),
                'total_tasks': data['total_tasks'],
                'days_tracked': len(data['logs'])
            })
        
        # Sort by week_start
        summary.sort(key=lambda x: x['week_start'])
        
        return {
            'weekly_summary': summary,
            'trends': self._calculate_trends(summary)
        }
    
    def get_daily_patterns(self, days: int = 30) -> Dict:
        """
        Analyze daily productivity patterns
        """
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        logs = self._get_logs_in_range(start_date, end_date)
        
        if not logs:
            return self._empty_daily_patterns()
        
        # Group by day of week
        daily_patterns = {i: [] for i in range(7)}  # 0=Monday, 6=Sunday
        
        for log in logs:
            day_of_week = log.date.weekday()
            daily_patterns[day_of_week].append({
                'score': log.productivity_score,
                'focus_ratio': log.focus_ratio,
                'hours_worked': log.hours_worked
            })
        
        # Calculate averages for each day
        patterns = []
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for day in range(7):
            day_data = daily_patterns[day]
            if day_data:
                avg_score = np.mean([d['score'] for d in day_data])
                avg_focus = np.mean([d['focus_ratio'] for d in day_data])
                avg_hours = np.mean([d['hours_worked'] for d in day_data])
                
                patterns.append({
                    'day': day_names[day],
                    'day_number': day,
                    'avg_productivity': round(avg_score, 1),
                    'avg_focus_ratio': round(avg_focus, 2),
                    'avg_hours_worked': round(avg_hours, 1),
                    'sample_size': len(day_data)
                })
        
        # Find best and worst days
        if patterns:
            best_day = max(patterns, key=lambda x: x['avg_productivity'])
            worst_day = min(patterns, key=lambda x: x['avg_productivity'])
        else:
            best_day = worst_day = None
        
        return {
            'daily_patterns': patterns,
            'best_day': best_day,
            'worst_day': worst_day,
            'recommendation': self._generate_pattern_recommendation(patterns)
        }
    
    def get_focus_analysis(self, days: int = 14) -> Dict:
        """
        Analyze focus patterns and distractions
        """
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        logs = self._get_logs_in_range(start_date, end_date)
        
        if not logs:
            return self._empty_focus_analysis()
        
        # Calculate focus metrics
        focus_ratios = [log.focus_ratio for log in logs]
        productive_hours = sum(log.focus_time for log in logs)
        total_hours = sum(log.hours_worked for log in logs)
        
        avg_focus_ratio = np.mean(focus_ratios) if focus_ratios else 0
        focus_consistency = 1 - (np.std(focus_ratios) if focus_ratios else 0)
        
        # Identify focus patterns
        high_focus_days = len([r for r in focus_ratios if r >= 0.8])
        low_focus_days = len([r for r in focus_ratios if r <= 0.5])
        
        return {
            'avg_focus_ratio': round(avg_focus_ratio, 2),
            'focus_consistency': round(focus_consistency, 2),
            'productive_hours': round(productive_hours, 1),
            'total_hours': round(total_hours, 1),
            'efficiency_ratio': round(productive_hours / total_hours, 2) if total_hours > 0 else 0,
            'high_focus_days': high_focus_days,
            'low_focus_days': low_focus_days,
            'focus_trend': self._calculate_focus_trend(logs),
            'recommendations': self._generate_focus_recommendations(avg_focus_ratio, focus_consistency)
        }
    
    def _get_logs_in_range(self, start_date, end_date):
        """Get productivity logs in date range"""
        from .user import ProductivityLog
        
        return ProductivityLog.query.filter(
            ProductivityLog.user_id == self.user_id,
            ProductivityLog.date >= start_date,
            ProductivityLog.date <= end_date
        ).all()
    
    def _calculate_trends(self, weekly_summary: List[Dict]) -> Dict:
        """Calculate productivity trends from weekly summary"""
        if len(weekly_summary) < 2:
            return {'direction': 'stable', 'change': 0}
        
        scores = [week['avg_productivity'] for week in weekly_summary]
        current_score = scores[-1]
        previous_score = scores[-2] if len(scores) > 1 else scores[0]
        
        change = current_score - previous_score
        percentage_change = (change / previous_score) * 100 if previous_score > 0 else 0
        
        if percentage_change > 5:
            direction = 'improving'
        elif percentage_change < -5:
            direction = 'declining'
        else:
            direction = 'stable'
        
        return {
            'direction': direction,
            'change': round(change, 1),
            'percentage_change': round(percentage_change, 1),
            'current_score': current_score,
            'previous_score': previous_score
        }
    
    def _calculate_focus_trend(self, logs: List) -> Dict:
        """Calculate focus trend over time"""
        if len(logs) < 2:
            return {'direction': 'stable', 'change': 0}
        
        # Split logs into first and second half for comparison
        mid_point = len(logs) // 2
        first_half = logs[:mid_point]
        second_half = logs[mid_point:]
        
        first_avg = np.mean([log.focus_ratio for log in first_half]) if first_half else 0
        second_avg = np.mean([log.focus_ratio for log in second_half]) if second_half else 0
        
        change = second_avg - first_avg
        percentage_change = (change / first_avg) * 100 if first_avg > 0 else 0
        
        if percentage_change > 10:
            direction = 'improving'
        elif percentage_change < -10:
            direction = 'declining'
        else:
            direction = 'stable'
        
        return {
            'direction': direction,
            'change': round(change, 2),
            'percentage_change': round(percentage_change, 1)
        }
    
    def _generate_pattern_recommendation(self, patterns: List[Dict]) -> str:
        """Generate recommendations based on daily patterns"""
        if not patterns:
            return "Track more data to get pattern-based recommendations."
        
        # Find significant variations
        scores = [p['avg_productivity'] for p in patterns]
        avg_score = np.mean(scores)
        std_score = np.std(scores)
        
        if std_score > 15:
            best_day = max(patterns, key=lambda x: x['avg_productivity'])
            return f"Your productivity peaks on {best_day['day']}. Schedule important tasks then."
        elif std_score < 5:
            return "Your productivity is consistent across days. Great job maintaining balance!"
        else:
            return "Consider aligning task difficulty with your higher productivity days."
    
    def _generate_focus_recommendations(self, avg_focus: float, consistency: float) -> List[str]:
        """Generate focus improvement recommendations"""
        recommendations = []
        
        if avg_focus < 0.6:
            recommendations.extend([
                "Try the Pomodoro technique (25min work, 5min break)",
                "Minimize distractions by turning off notifications",
                "Create a dedicated workspace"
            ])
        elif avg_focus < 0.8:
            recommendations.extend([
                "Your focus is good, but there's room for improvement",
                "Consider time-blocking for deep work sessions",
                "Take regular breaks to maintain focus"
            ])
        else:
            recommendations.append("Excellent focus levels! Maintain your current habits.")
        
        if consistency < 0.7:
            recommendations.append("Work on maintaining consistent focus across days")
        
        return recommendations
    
    def _empty_weekly_summary(self, weeks: int) -> Dict:
        """Return empty weekly summary structure"""
        return {
            'weekly_summary': [],
            'trends': {'direction': 'stable', 'change': 0}
        }
    
    def _empty_daily_patterns(self) -> Dict:
        """Return empty daily patterns structure"""
        return {
            'daily_patterns': [],
            'best_day': None,
            'worst_day': None,
            'recommendation': "Insufficient data for pattern analysis"
        }
    
    def _empty_focus_analysis(self) -> Dict:
        """Return empty focus analysis structure"""
        return {
            'avg_focus_ratio': 0,
            'focus_consistency': 0,
            'productive_hours': 0,
            'total_hours': 0,
            'efficiency_ratio': 0,
            'high_focus_days': 0,
            'low_focus_days': 0,
            'focus_trend': {'direction': 'stable', 'change': 0},
            'recommendations': ["Start tracking your work to get focus insights"]
        }

class ProductivityCalculator:
    """
    Calculate various productivity metrics and scores
    """
    
    @staticmethod
    def calculate_comprehensive_score(logs: List) -> float:
        """
        Calculate comprehensive productivity score considering multiple factors
        """
        if not logs:
            return 75.0  # Default score
        
        # Extract metrics
        scores = [log.productivity_score for log in logs]
        focus_ratios = [log.focus_ratio for log in logs]
        efficiencies = [log.task_efficiency for log in logs]
        
        # Calculate weighted score
        avg_score = np.mean(scores)
        avg_focus = np.mean(focus_ratios)
        avg_efficiency = np.mean(efficiencies)
        
        # Consistency bonus (lower std deviation = higher consistency)
        score_std = np.std(scores) if len(scores) > 1 else 0
        consistency_bonus = max(0, 10 - score_std)
        
        # Focus bonus
        focus_bonus = 5 if avg_focus > 0.8 else 0
        
        comprehensive_score = (avg_score * 0.7 + avg_efficiency * 0.3 + 
                             consistency_bonus + focus_bonus)
        
        return min(100, max(0, comprehensive_score))
    
    @staticmethod
    def calculate_burnout_risk(logs: List) -> Dict:
        """
        Calculate burnout risk based on work patterns
        """
        if len(logs) < 7:
            return {'risk_level': 'low', 'score': 0, 'factors': []}
        
        recent_logs = logs[-7:]  # Last 7 days
        
        # Calculate risk factors
        total_hours = sum(log.hours_worked for log in recent_logs)
        avg_hours = total_hours / 7
        
        # Productivity decline
        first_half = recent_logs[:3]
        second_half = recent_logs[3:]
        first_avg = np.mean([log.productivity_score for log in first_half]) if first_half else 0
        second_avg = np.mean([log.productivity_score for log in second_half]) if second_half else 0
        productivity_decline = first_avg - second_avg
        
        # Focus decline
        first_focus = np.mean([log.focus_ratio for log in first_half]) if first_half else 0
        second_focus = np.mean([log.focus_ratio for log in second_half]) if second_half else 0
        focus_decline = first_focus - second_focus
        
        # Calculate risk score
        risk_score = 0
        factors = []
        
        if avg_hours > 9:
            risk_score += 30
            factors.append("High average daily hours")
        
        if productivity_decline > 10:
            risk_score += 25
            factors.append("Significant productivity decline")
        
        if focus_decline > 0.1:
            risk_score += 20
            factors.append("Focus ratio declining")
        
        if total_hours > 60:  # More than 60 hours per week
            risk_score += 25
            factors.append("Excessive weekly hours")
        
        # Determine risk level
        if risk_score >= 60:
            risk_level = 'high'
        elif risk_score >= 30:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return {
            'risk_level': risk_level,
            'score': risk_score,
            'factors': factors,
            'recommendation': ProductivityCalculator._get_burnout_recommendation(risk_level)
        }
    
    @staticmethod
    def _get_burnout_recommendation(risk_level: str) -> str:
        """Get burnout prevention recommendation based on risk level"""
        recommendations = {
            'low': "Your work patterns look healthy. Maintain good work-life balance.",
            'medium': "Consider taking breaks and varying your tasks to prevent burnout.",
            'high': "High burnout risk detected. Please take time to rest and recover."
        }
        return recommendations.get(risk_level, "Monitor your work patterns.")
    
    @staticmethod
    def calculate_improvement_potential(logs: List) -> Dict:
        """
        Calculate potential for productivity improvement
        """
        if len(logs) < 14:
            return {'potential': 'unknown', 'score': 0, 'areas': []}
        
        recent_logs = logs[-14:]  # Last 14 days
        
        improvement_areas = []
        potential_score = 0
        
        # Analyze focus ratio
        avg_focus = np.mean([log.focus_ratio for log in recent_logs])
        if avg_focus < 0.7:
            improvement_areas.append("Focus ratio below optimal level")
            potential_score += (0.7 - avg_focus) * 50
        
        # Analyze task efficiency
        avg_efficiency = np.mean([log.task_efficiency for log in recent_logs])
        if avg_efficiency < 80:
            improvement_areas.append("Task efficiency can be improved")
            potential_score += (80 - avg_efficiency) * 0.5
        
        # Analyze consistency
        scores = [log.productivity_score for log in recent_logs]
        consistency = 1 - (np.std(scores) / 100) if len(scores) > 1 else 1
        if consistency < 0.8:
            improvement_areas.append("Productivity consistency needs work")
            potential_score += (0.8 - consistency) * 40
        
        # Determine potential level
        if potential_score >= 30:
            potential_level = 'high'
        elif potential_score >= 15:
            potential_level = 'medium'
        else:
            potential_level = 'low'
        
        return {
            'potential': potential_level,
            'score': round(potential_score, 1),
            'areas': improvement_areas,
            'estimated_improvement': min(25, potential_score)  # Max 25% estimated improvement
        }