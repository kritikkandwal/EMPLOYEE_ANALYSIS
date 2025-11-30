# routes/attendance_api.py
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
import calendar
import random
from sqlalchemy import and_
from models import db
from models.attendance import AttendanceLog
from models.attendance_models.predict_attendance import predictor

attendance_api_bp = Blueprint("attendance_api", __name__)

def _last_day_of_month(year, month):
    return calendar.monthrange(year, month)[1]


def _build_calendar_for_month(year, month, logs):
    """
    Builds a month calendar (weeks list) from 'logs' which may be dicts
    or AttendanceLog instances. Kept for compatibility if you need it.
    """
    by_date = {}
    for l in logs:
        if isinstance(l, dict):
            rec = l
        else:
            rec = l.to_dict()
        by_date[rec["date"]] = rec

    weeks = []
    first_weekday, days_in_month = calendar.monthrange(year, month)

    day_cells = []
    for _ in range(first_weekday):
        day_cells.append(None)

    for d in range(1, days_in_month + 1):
        iso = date(year, month, d).isoformat()
        rec = by_date.get(iso)
        is_weekend = date(year, month, d).weekday() >= 5
        if rec:
            status = rec.get("status", "absent")
            hours = rec.get("hours_worked", 0)
            prod = rec.get("productivity_score", 0)
        else:
            status = "weekend" if is_weekend else "absent"
            hours = 0
            prod = 0

        day_cells.append({
            "date": iso,
            "day": d,
            "status": status,
            "hours_worked": hours,
            "productivity_score": prod,
            "is_weekend": is_weekend
        })

    week = []
    for cell in day_cells:
        week.append(cell)
        if len(week) == 7:
            weeks.append(week)
            week = []

    if week:
        while len(week) < 7:
            week.append(None)
        weeks.append(week)

    return weeks


def _compute_stats_from_records(records):
    """
    Compute present days, total hours, attendance rate, and current streak
    given a list of daily records for days that were considered (typically
    days up to today).
    """
    # Only consider records that are not future placeholders
    if not records:
        return {
            "present_days": 0,
            "total_hours": 0,
            "attendance_rate": 0,
            "current_streak": 0
        }

    # Only count days that are actual days (we assume records list contains days up to today)
    present_days = sum(1 for r in records if r.get("status") == "present")
    total_hours = sum(float(r.get("hours_worked") or 0) for r in records)
    # working_days should be days considered (not including future days)
    working_days = len(records)

    attendance_rate = round((present_days / working_days) * 100, 0) if working_days > 0 else 0

    # current streak: look backwards from most recent day (today or last available)
    sorted_by_date = sorted(records, key=lambda r: r.get("date"), reverse=True)
    streak = 0
    for rec in sorted_by_date:
        if rec.get("status") == "present":
            streak += 1
        else:
            break

    return {
        "present_days": int(present_days),
        "total_hours": round(total_hours, 2),
        "attendance_rate": int(attendance_rate),
        "current_streak": int(streak)
    }


def _get_month_records(user_id, year, month):
    """
    Return a list of daily records for the given user/month combining:
      - real AttendanceLog DB rows (for any days that exist)
      - random-generated placeholders for days that have no DB rows
    The returned list contains only days <= today (so future days are ignored)
    and is sorted ascending by date.
    
    Each record: { "date": "YYYY-MM-DD", "hours_worked": float, "status": "present|half-day|absent" }
    """
    records = []
    today = date.today()
    days_in_month = calendar.monthrange(year, month)[1]

    # Query DB logs for this user and month
    month_start = date(year, month, 1)
    month_end = date(year, month, days_in_month)

    # We'll only include days up to min(month_end, today)
    effective_end = month_end if month_end <= today else today

    # Fetch attendance rows in DB for the range [month_start, effective_end]
    db_logs = AttendanceLog.query.filter(
        AttendanceLog.user_id == user_id,
        AttendanceLog.date >= month_start,
        AttendanceLog.date <= effective_end
    ).all()

    db_map = {log.date.isoformat(): log.to_dict() for log in db_logs}

    # Build records for each day from 1 .. effective_end.day
    for d in range(1, effective_end.day + 1):
        dt = date(year, month, d)
        iso = dt.isoformat()

        if iso in db_map:
            # prefer DB record (real current-day or any day that exists)
            rec = db_map[iso]
            # make sure keys exist and have expected types
            records.append({
                "date": iso,
                "hours_worked": float(rec.get("hours_worked") or 0),
                "status": rec.get("status") or "absent",
                "source": "db"
            })
            continue

        # No DB row -> generate a random record (preserve existing random behavior)
        # Keep the same probabilistic distribution implemented in frontend
        rnd = random.random()
        hours = 0
        status = "absent"
        if rnd > 0.7:
            status = "present"
            hours = float(random.randint(6, 9))
        elif rnd > 0.5:
            status = "half-day"
            hours = float(random.randint(3, 5))
        else:
            status = "absent"
            hours = 0.0

        records.append({
            "date": iso,
            "hours_worked": hours,
            "status": status,
            "source": "random"
        })

    # Return sorted ascending by date
    records = sorted(records, key=lambda r: r["date"])
    return records


@attendance_api_bp.route("/current-status")
@login_required
def current_status():
    """
    Returns today's status (as before) PLUS combined monthly statistics for the current month.
    Frontend can use .present_days_month / .attendance_rate_month / .total_hours_month / .current_streak_month
    to populate the Monthly Statistics UI. Daily per-day behaviour (today) remains the same.
    """
    today = date.today()

    log = AttendanceLog.query.filter_by(
        user_id=current_user.id,
        date=today
    ).first()

    if not log:
        # Compose monthly records (combining DB and random) for the current month
        month_records = _get_month_records(current_user.id, today.year, today.month)
        stats = _compute_stats_from_records(month_records)

        return jsonify({
            "logged_in": False,
            "present_days": 0,
            "total_hours": 0,
            "status": "absent",
            "login_time": None,
            "logout_time": None,
            "today": None,
            # monthly aggregates (new fields)
            "present_days_month": stats["present_days"],
            "total_hours_month": stats["total_hours"],
            "attendance_rate_month": stats["attendance_rate"],
            "current_streak_month": stats["current_streak"]
        })

    today_obj = log.to_dict()

    # compute combined monthly stats (incl. random for past days)
    month_records = _get_month_records(current_user.id, today.year, today.month)
    stats = _compute_stats_from_records(month_records)

    return jsonify({
        "logged_in": log.login_time is not None,
        "present_days": 1 if log.status == "present" else 0,
        "total_hours": log.hours_worked,
        "status": log.status,
        "login_time": log.login_time.isoformat() if log.login_time else None,
        "logout_time": log.logout_time.isoformat() if log.logout_time else None,
        "today": today_obj,
        # monthly aggregates (new fields)
        "present_days_month": stats["present_days"],
        "total_hours_month": stats["total_hours"],
        "attendance_rate_month": stats["attendance_rate"],
        "current_streak_month": stats["current_streak"]
    })


def _do_login(user_id):
    today = date.today()
    log = AttendanceLog.query.filter_by(user_id=user_id, date=today).first()
    if not log:
        log = AttendanceLog(user_id=user_id, date=today, login_time=datetime.now(), status="present")
        db.session.add(log)
    else:
        log.login_time = datetime.now()
        log.status = "present"
    db.session.commit()
    return {"success": True, "message": "Logged In Successfully", "today": log.to_dict()}


def _do_logout(user_id):
    today = date.today()
    log = AttendanceLog.query.filter_by(user_id=user_id, date=today).first()
    if not log:
        return {"success": False, "message": "You haven't logged in today"}, 400

    log.logout_time = datetime.now()
    if log.login_time:
        delta = log.logout_time - log.login_time
        log.hours_worked = round(delta.total_seconds() / 3600, 2)

    log.calculate_status()
    log.calculate_productivity()
    db.session.commit()
    return {"success": True, "message": "Logged Out Successfully", "today": log.to_dict()}


@attendance_api_bp.route("/mark", methods=["POST"])
@login_required
def mark_attendance():
    data = request.get_json(force=True, silent=True) or {}
    action = data.get("action")
    if action == "login":
        return jsonify(_do_login(current_user.id))
    if action == "logout":
        result = _do_logout(current_user.id)
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]
        return jsonify(result)
    return jsonify({"success": False, "message": "Invalid action"}), 400


@attendance_api_bp.route("/log", methods=["POST"])
@login_required
def log_alias():
    return mark_attendance()


@attendance_api_bp.route("/monthly")
@login_required
def monthly_attendance_fake():
    """
    Returns the list of records for the requested year/month for the current_user.
    This function now uses _get_month_records so DB entries override random generation and
    the frontend heatmap receives combined data.
    """
    try:
        year = int(request.args.get("year"))
        month = int(request.args.get("month"))

        records = _get_month_records(current_user.id, year, month)
        # The frontend heatmap expects records (date, hours_worked, status)
        return jsonify({"success": True, "records": records})
    except Exception as e:
        return jsonify({"success": False, "records": [], "error": str(e)})


# ----------------------------------------------------
# ONLY KEEP THIS PREDICTIONS ROUTE
# ----------------------------------------------------
@attendance_api_bp.route("/predictions")
@login_required
def attendance_predictions():
    try:
        preds = predictor.predict_all()

        next_week = preds.get("next_week_forecast") or []
        week_list = []
        for i, val in enumerate(next_week):
            dt = (date.today() + timedelta(days=i + 1))
            week_list.append({
                "day": dt.strftime("%a"),
                "date": dt.isoformat(),
                "probability": round(float(val) * 100, 1)
            })

        tomorrow_val = float(preds.get("average_prediction", 0))

        absence_prob = preds.get("absence_likelihood", 1 - tomorrow_val)
        risk = "low"
        if absence_prob > 0.4:
            risk = "high"
        elif absence_prob > 0.25:
            risk = "medium"

        response = {
            "success": True,
            "predictions": {
                "tomorrow_prediction": {
                    "probability": round(tomorrow_val * 100, 1),
                    "expected_hours": preds.get("expected_hours", 0),
                    "confidence": preds.get("confidence", "medium"),
                    "model_used": preds.get("model_used", "ensemble")
                },
                "weekly_trend": week_list,
                "streak_analysis": {
                    "current_streak": preds.get("streak_prediction", 0),
                    "probability_continue": 0,
                    "expected_end_in": 0
                },
                "absence_likelihood": {
                    "risk_level": risk,
                    "probability": round(absence_prob, 3),
                    "factors": preds.get("absence_factors", [])
                }
            }
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# NEW ROUTE — Insights block
@attendance_api_bp.route("/insights")
@login_required
def attendance_insights():
    try:
        raw = predictor.predict_all()

        insights = {
            "predicted_attendance_rate": int(raw["average_prediction"] * 100),
            "confidence_score": round(raw.get("confidence", 0.6), 2),
            "recommended_improvements": [
                "Try maintaining consistent working hours pattern",
                "Consider improving productivity score on low days",
                "Avoid long gaps between login and logout timings"
            ]
        }

        return jsonify({"success": True, "insights": insights})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@attendance_api_bp.route("/generate-sample-data")
@login_required
def generate_sample_data():
    try:
        df = predictor.create_sample_data()
        return jsonify({"success": True, "message": "Sample data created", "records": len(df)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
