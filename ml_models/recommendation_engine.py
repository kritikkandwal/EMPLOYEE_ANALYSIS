"""
AI-powered recommendation engine for productivity improvement
"""
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
from models.user import ProductivityLog

logger = logging.getLogger(__name__)

class RecommendationEngine:
    """
    Generate personalized productivity recommendations using AI
    """
    
    def __init__(self):
        self.recommendation_templates = self._load_recommendation_templates()
    
    def generate_recommendations(self, user, logs: List[ProductivityLog]) -> List[Dict[str, Any]]:
        """
        Generate personalized recommendations based on user data
        """
        try:
            if not logs:
                return self._get_general_recommendations()
            
            recommendations = []
            
            # Analyze different aspects of productivity
            recommendations.extend(self._analyze_focus_patterns(logs))
            recommendations.extend(self._analyze_time_management(logs))
            recommendations.extend(self._analyze_task_efficiency(logs))
            recommendations.extend(self._analyze_work_patterns(logs))
            recommendations.extend(self._analyze_wellbeing(logs))
            
            # Remove duplicates and limit to top recommendations
            unique_recommendations = []
            seen_messages = set()
            
            for rec in recommendations:
                if rec['message'] not in seen_messages:
                    unique_recommendations.append(rec)
                    seen_messages.add(rec['message'])
            
            # Sort by priority and return top 5
            unique_recommendations.sort(key=lambda x: x['priority'], reverse=True)
            return unique_recommendations[:5]
            
        except Exception as e:
            logger.error(f"Recommendation generation error: {e}")
            return self._get_fallback_recommendations()
    
    def _analyze_focus_patterns(self, logs: List[ProductivityLog]) -> List[Dict[str, Any]]:
        """Analyze focus patterns and generate recommendations"""
        recommendations = []
        
        if len(logs) < 3:
            return recommendations
        
        # Calculate average focus ratio
        focus_ratios = [log.focus_ratio for log in logs]
        avg_focus = sum(focus_ratios) / len(focus_ratios)
        
        # Focus-based recommendations
        if avg_focus < 0.6:
            recommendations.append({
                'type': 'focus',
                'priority': 9,
                'message': 'Your focus ratio is below optimal. Try minimizing distractions during work sessions.',
                'action': 'Implement the Pomodoro technique',
                'impact': 'high'
            })
        elif avg_focus < 0.75:
            recommendations.append({
                'type': 'focus',
                'priority': 7,
                'message': 'Good focus levels. Consider time-blocking for complex tasks.',
                'action': 'Schedule deep work sessions',
                'impact': 'medium'
            })
        
        # Focus consistency
        focus_std = self._calculate_std(focus_ratios)
        if focus_std > 0.2:
            recommendations.append({
                'type': 'consistency',
                'priority': 8,
                'message': 'Your focus levels vary significantly. Work on maintaining consistent focus.',
                'action': 'Establish a daily routine',
                'impact': 'high'
            })
        
        return recommendations
    
    def _analyze_time_management(self, logs: List[ProductivityLog]) -> List[Dict[str, Any]]:
        """Analyze time management patterns"""
        recommendations = []
        
        if len(logs) < 5:
            return recommendations
        
        # Analyze work hours
        work_hours = [log.hours_worked for log in logs]
        avg_hours = sum(work_hours) / len(work_hours)
        
        if avg_hours > 9:
            recommendations.append({
                'type': 'wellbeing',
                'priority': 9,
                'message': 'You\'re working long hours. Consider balancing work and rest to prevent burnout.',
                'action': 'Set strict work hour boundaries',
                'impact': 'high'
            })
        elif avg_hours < 5:
            recommendations.append({
                'type': 'efficiency',
                'priority': 6,
                'message': 'Shorter work days detected. Focus on maximizing productivity during active hours.',
                'action': 'Use time-blocking for important tasks',
                'impact': 'medium'
            })
        
        # Analyze productivity per hour
        productivity_per_hour = [
            log.productivity_score / log.hours_worked if log.hours_worked > 0 else 0 
            for log in logs
        ]
        avg_pph = sum(productivity_per_hour) / len(productivity_per_hour)
        
        if avg_pph < 10:
            recommendations.append({
                'type': 'efficiency',
                'priority': 8,
                'message': 'Low productivity per hour. Consider optimizing your work methods.',
                'action': 'Review and streamline workflows',
                'impact': 'high'
            })
        
        return recommendations
    
    def _analyze_task_efficiency(self, logs: List[ProductivityLog]) -> List[Dict[str, Any]]:
        """Analyze task completion efficiency"""
        recommendations = []
        
        if len(logs) < 3:
            return recommendations
        
        # Calculate task efficiency
        efficiencies = [log.task_efficiency for log in logs if log.task_efficiency]
        if not efficiencies:
            return recommendations
        
        avg_efficiency = sum(efficiencies) / len(efficiencies)
        
        if avg_efficiency < 70:
            recommendations.append({
                'type': 'efficiency',
                'priority': 8,
                'message': 'Task completion rate can be improved. Break down complex tasks into smaller steps.',
                'action': 'Use task decomposition technique',
                'impact': 'high'
            })
        
        # Analyze efficiency trend
        if len(efficiencies) >= 7:
            recent_eff = efficiencies[-3:]
            older_eff = efficiencies[-7:-4]
            recent_avg = sum(recent_eff) / len(recent_eff)
            older_avg = sum(older_eff) / len(older_eff)
            
            if recent_avg < older_avg - 10:
                recommendations.append({
                    'type': 'trend',
                    'priority': 7,
                    'message': 'Task efficiency is declining. Identify and address potential blockers.',
                    'action': 'Conduct a workflow review',
                    'impact': 'medium'
                })
        
        return recommendations
    
    def _analyze_work_patterns(self, logs: List[ProductivityLog]) -> List[Dict[str, Any]]:
        """Analyze overall work patterns and habits"""
        recommendations = []
        
        if len(logs) < 7:
            return recommendations
        
        # Check for consistency
        scores = [log.productivity_score for log in logs]
        consistency = 1 - (self._calculate_std(scores) / 100)
        
        if consistency < 0.7:
            recommendations.append({
                'type': 'consistency',
                'priority': 7,
                'message': 'Productivity levels vary significantly. Establish more consistent work habits.',
                'action': 'Create and follow a daily routine',
                'impact': 'medium'
            })
        
        # Identify peak performance times (simplified)
        morning_scores = [log.productivity_score for log in logs if log.date.hour < 12]
        afternoon_scores = [log.productivity_score for log in logs if 12 <= log.date.hour < 17]
        
        if morning_scores and afternoon_scores:
            morning_avg = sum(morning_scores) / len(morning_scores)
            afternoon_avg = sum(afternoon_scores) / len(afternoon_scores)
            
            if morning_avg > afternoon_avg + 10:
                recommendations.append({
                    'type': 'scheduling',
                    'priority': 6,
                    'message': 'You perform better in mornings. Schedule important tasks before noon.',
                    'action': 'Plan critical work for morning hours',
                    'impact': 'medium'
                })
            elif afternoon_avg > morning_avg + 10:
                recommendations.append({
                    'type': 'scheduling',
                    'priority': 6,
                    'message': 'Afternoons are your peak performance time. Leverage this for complex tasks.',
                    'action': 'Reschedule important work to afternoons',
                    'impact': 'medium'
                })
        
        return recommendations
    
    def _analyze_wellbeing(self, logs: List[ProductivityLog]) -> List[Dict[str, Any]]:
        """Analyze wellbeing and work-life balance"""
        recommendations = []
        
        if len(logs) < 7:
            return recommendations
        
        # Check for burnout risk
        recent_scores = [log.productivity_score for log in logs[-3:]]
        older_scores = [log.productivity_score for log in logs[-7:-4]]
        
        if recent_scores and older_scores:
            recent_avg = sum(recent_scores) / len(recent_scores)
            older_avg = sum(older_scores) / len(older_scores)
            
            if recent_avg < older_avg - 15:
                recommendations.append({
                    'type': 'wellbeing',
                    'priority': 9,
                    'message': 'Significant productivity drop detected. Consider taking a break to recharge.',
                    'action': 'Schedule downtime and self-care',
                    'impact': 'high'
                })
        
        # Check for overwork
        total_hours_week = sum(log.hours_worked for log in logs[-7:])
        if total_hours_week > 50:
            recommendations.append({
                'type': 'wellbeing',
                'priority': 8,
                'message': 'High weekly hours detected. Maintain work-life balance for sustained productivity.',
                'action': 'Set boundaries and take regular breaks',
                'impact': 'high'
            })
        
        return recommendations
    
    def _calculate_std(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def _load_recommendation_templates(self) -> Dict[str, List[str]]:
        """Load recommendation message templates"""
        return {
            'focus': [
                "Improve your focus by minimizing digital distractions during work sessions",
                "Consider using focus-enhancing techniques like the Pomodoro method",
                "Your focus ratio suggests room for improvement in maintaining concentration"
            ],
            'efficiency': [
                "Optimize your task completion rate by breaking down complex projects",
                "Streamline your workflow to improve task efficiency",
                "Consider time-blocking for better task management"
            ],
            'consistency': [
                "Work on maintaining more consistent productivity levels",
                "Establishing a routine can help stabilize your daily performance",
                "Your productivity varies significantly - focus on consistency"
            ],
            'scheduling': [
                "Align your task schedule with your natural energy patterns",
                "Schedule demanding tasks during your peak performance hours",
                "Optimize your daily schedule based on productivity patterns"
            ],
            'wellbeing': [
                "Prioritize work-life balance for sustained productivity",
                "Regular breaks and self-care are essential for long-term performance",
                "Monitor your workload to prevent burnout and maintain health"
            ]
        }
    
    def _get_general_recommendations(self) -> List[Dict[str, Any]]:
        """Get general recommendations for new users"""
        return [
            {
                'type': 'general',
                'priority': 5,
                'message': 'Start tracking your work patterns to get personalized recommendations',
                'action': 'Log your daily productivity metrics',
                'impact': 'medium'
            },
            {
                'type': 'general',
                'priority': 4,
                'message': 'Establish a consistent work routine for better productivity tracking',
                'action': 'Set regular work hours',
                'impact': 'medium'
            }
        ]
    
    def _get_fallback_recommendations(self) -> List[Dict[str, Any]]:
        """Get fallback recommendations in case of errors"""
        return [
            {
                'type': 'general',
                'priority': 5,
                'message': 'Focus on maintaining consistent work habits for better productivity',
                'action': 'Establish a daily routine',
                'impact': 'medium'
            }
        ]
    
    def calculate_recommendation_confidence(self, logs: List[ProductivityLog]) -> float:
        """
        Calculate confidence score for recommendations based on data quality
        """
        if len(logs) < 7:
            return 0.6  # Medium confidence for limited data
        
        # Higher confidence with more data and consistent patterns
        data_points = len(logs)
        consistency = 1 - (self._calculate_std([log.productivity_score for log in logs]) / 100)
        
        confidence = min(0.95, 0.5 + (data_points / 30) * 0.3 + consistency * 0.2)
        return round(confidence, 2)