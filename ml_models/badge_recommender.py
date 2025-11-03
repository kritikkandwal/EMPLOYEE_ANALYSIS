from datetime import datetime, time
import numpy as np

class BadgeRecommender:
    def __init__(self):
        self.badge_rules = {
            'early_bird': self._check_early_bird,
            'focus_master': self._check_focus_master,
            'consistency_king': self._check_consistency_king,
            'deadline_crusher': self._check_deadline_crusher,
            'improvement_champ': self._check_improvement_champ,
            'night_owl': self._check_night_owl,
            'marathon_worker': self._check_marathon_worker,
            'task_maestro': self._check_task_maestro
        }
    
    def recommend_badges(self, user, productivity_logs, recent_days=30):
        """Recommend badges based on user performance"""
        badges = []
        
        for badge_type, check_function in self.badge_rules.items():
            if check_function(user, productivity_logs, recent_days):
                badge_info = self._get_badge_info(badge_type)
                badges.append(badge_info)
        
        return badges
    
    def _check_early_bird(self, user, logs, days):
        """Check if user consistently logs in early"""
        early_count = 0
        for log in logs[-days:]:
            # Simplified: assume early if high productivity in morning hours
            if log.productivity_score > 80:
                early_count += 1
        
        return early_count >= (days * 0.7)  # 70% of days
    
    def _check_focus_master(self, user, logs, days):
        """Check if user maintains high focus ratio"""
        if len(logs) < 7:  # Need at least a week of data
            return False
        
        recent_logs = logs[-days:]
        avg_focus = sum(log.focus_ratio for log in recent_logs) / len(recent_logs)
        return avg_focus >= 0.85
    
    def _check_consistency_king(self, user, logs, days):
        """Check if user maintains high productivity consistently"""
        if len(logs) < 14:
            return False
        
        recent_scores = [log.productivity_score for log in logs[-days:]]
        avg_score = np.mean(recent_scores)
        std_score = np.std(recent_scores)
        
        return avg_score >= 80 and std_score <= 10
    
    def _check_deadline_crusher(self, user, logs, days):
        """Check if user completes tasks on time"""
        recent_logs = logs[-days:]
        total_tasks = sum(log.tasks_assigned for log in recent_logs)
        completed_tasks = sum(log.tasks_completed for log in recent_logs)
        
        if total_tasks == 0:
            return False
        
        completion_rate = completed_tasks / total_tasks
        return completion_rate >= 0.95
    
    def _check_improvement_champ(self, user, logs, days):
        """Check if user shows consistent improvement"""
        if len(logs) < 28:  # Need at least 4 weeks
            return False
        
        # Calculate trend over recent period
        recent_scores = [log.productivity_score for log in logs[-days:]]
        if len(recent_scores) < 2:
            return False
        
        x = np.arange(len(recent_scores))
        slope = np.polyfit(x, recent_scores, 1)[0]
        return slope > 1.0  # Positive trend of at least 1 point per period
    
    def _check_night_owl(self, user, logs, days):
        """Check if user performs better in late hours"""
        # Simplified implementation
        recent_logs = logs[-min(14, len(logs)):]  # Last 14 days
        if len(recent_logs) < 7:
            return False
        
        # In real implementation, check actual login times
        return len(recent_logs) >= 10  # Placeholder
    
    def _check_marathon_worker(self, user, logs, days):
        """Check for long productive streaks"""
        recent_logs = logs[-min(30, len(logs)):]
        current_streak = 0
        max_streak = 0
        
        for log in recent_logs:
            if log.productivity_score >= 70:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        return max_streak >= 7  # 7-day streak
    
    def _check_task_maestro(self, user, logs, days):
        """Check for high task completion volume"""
        recent_logs = logs[-days:]
        total_tasks = sum(log.tasks_completed for log in recent_logs)
        return total_tasks >= 50  # 50 tasks in the period
    
    def _get_badge_info(self, badge_type):
        """Get badge information"""
        badge_info = {
            'early_bird': {
                'name': 'Early Bird',
                'description': 'Consistently productive in morning hours',
                'level': 'gold'
            },
            'focus_master': {
                'name': 'Focus Master',
                'description': 'Maintains exceptional focus ratio',
                'level': 'platinum'
            },
            'consistency_king': {
                'name': 'Consistency King',
                'description': 'Sustains high productivity consistently',
                'level': 'diamond'
            },
            'deadline_crusher': {
                'name': 'Deadline Crusher',
                'description': 'Always completes tasks before deadlines',
                'level': 'gold'
            },
            'improvement_champ': {
                'name': 'Improvement Champion',
                'description': 'Shows continuous productivity improvement',
                'level': 'silver'
            },
            'night_owl': {
                'name': 'Night Owl',
                'description': 'Peak performance during late hours',
                'level': 'bronze'
            },
            'marathon_worker': {
                'name': 'Marathon Worker',
                'description': 'Longest productive streak without breaks',
                'level': 'gold'
            },
            'task_maestro': {
                'name': 'Task Maestro',
                'description': 'Highest number of tasks completed',
                'level': 'platinum'
            }
        }
        
        return badge_info.get(badge_type, {
            'name': 'Achiever',
            'description': 'Great work!',
            'level': 'bronze'
        })