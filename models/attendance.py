from datetime import datetime, date
from .database import db

class AttendanceLog(db.Model):
    __tablename__ = "attendance_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)

    login_time = db.Column(db.DateTime)
    logout_time = db.Column(db.DateTime)
    hours_worked = db.Column(db.Float, default=0.0)

    status = db.Column(db.String(20), default="absent")
    productivity_score = db.Column(db.Float, default=0.0)

    def calculate_status(self):
        if self.hours_worked >= 8:
            self.status = "present"
        elif 4 <= self.hours_worked < 8:
            self.status = "half-day"
        else:
            self.status = "absent"

    def calculate_productivity(self):
        if self.hours_worked <= 0:
            self.productivity_score = 0
        else:
            # simple formula: hours worked × 10
            self.productivity_score = min(100, self.hours_worked * 10)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "date": self.date.isoformat(),
            "login_time": self.login_time.isoformat() if self.login_time else None,
            "logout_time": self.logout_time.isoformat() if self.logout_time else None,
            "hours_worked": self.hours_worked,
            "status": self.status,
            "productivity_score": self.productivity_score
        }
