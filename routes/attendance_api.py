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
from models.attendance_models.attendance_cache import (
    load_cache, save_cache, set_day, get_day, ensure_history_exists
)


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

@attendance_api_bp.route("/monthly-stats")
@login_required
def monthly_stats():
    try:
        year = int(request.args.get("year"))
        month = int(request.args.get("month"))

        records = _get_month_records(current_user.id, year, month)
        stats = _compute_stats_from_records(records)

        return jsonify({
            "success": True,
            "stats": stats
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


def _compute_stats_from_records(records):
    """
    Compute present days, total hours, attendance rate, and current streak
    given a list of daily records (records must be sorted ascending by date).
    Attendance rate is calculated over WORKING DAYS (exclude weekends).
    """
    if not records:
        return {
            "present_days": 0,
            "total_hours": 0,
            "attendance_rate": 0,
            "current_streak": 0
        }

    # total present days
    present_days = sum(1 for r in records if r.get("status") == "present")

    # total hours (sum hours_worked)
    total_hours = sum(float(r.get("hours_worked") or 0) for r in records)

    # working_days: exclude weekend entries (status == 'weekend' OR is_weekend True)
    working_days = sum(1 for r in records if not (r.get("status") == "weekend" or r.get("is_weekend")))

    attendance_rate = round((present_days / working_days) * 100, 0) if working_days > 0 else 0

    # current streak: look backwards from most recent day (records assumed ascending)
    # stop when a non-present weekday is encountered (weekends break streak)
    sorted_by_date_desc = sorted(records, key=lambda r: r.get("date"), reverse=True)
    streak = 0
    for rec in sorted_by_date_desc:
        # ignore future days (records should not contain future, but keep safe)
        # break on weekends (treat weekends as break) or first non-present weekday
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
      - cache entries (preferred)
      - if cache missing a day -> fill with sensible default
    The returned list contains only days <= today (so future days are ignored)
    and is sorted ascending by date.

    Each record: {
        "date": "YYYY-MM-DD",
        "hours_worked": float,
        "status": "present|half-day|absent|weekend",
        "is_weekend": bool,
        "source": "cache" | "default"
    }
    """
    cache = ensure_history_exists(user_id)  # creates static history if missing

    records = []
    today = date.today()
    days_in_month = calendar.monthrange(year, month)[1]

    # iterate every day of the month but only up to today
    for d in range(1, days_in_month + 1):
        dt = date(year, month, d)
        if dt > today:
            break

        iso = dt.isoformat()
        entry = cache.get(iso)

        if entry:
            # Cache uses keys: "status" and "hours"
            records.append({
                "date": iso,
                "hours_worked": float(entry.get("hours", 0)),
                "status": entry.get("status", "absent"),
                "is_weekend": dt.weekday() >= 5,
                "source": "cache"
            })
        else:
            # No cache entry -> default placeholder (keeps heatmap & stats consistent)
            is_weekend = dt.weekday() >= 5
            default_status = "weekend" if is_weekend else "absent"
            records.append({
                "date": iso,
                "hours_worked": 0.0,
                "status": default_status,
                "is_weekend": is_weekend,
                "source": "default"
            })

    # sort by date ascending
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

    # 🔥 NEW — Save to CACHE
    set_day(user_id, today, "present", 0)

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

    # 🔥 NEW — Save to CACHE after computing hours + status
    set_day(user_id, today, log.status, log.hours_worked)

    return {"success": True, "message": "Logged Out Successfully", "today": log.to_dict()}


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

        # -------------------------------
        # WEEK FORECAST
        # -------------------------------
        next_week = preds.get("next_week_forecast") or []
        week_list = []
        for i, val in enumerate(next_week):
            dt = (date.today() + timedelta(days=i + 1))
            week_list.append({
                "day": dt.strftime("%a"),
                "date": dt.isoformat(),
                "probability": round(float(val) * 100, 1)
            })

        # -------------------------------
        # TOMORROW PREDICTION
        # -------------------------------
        tomorrow_val = float(preds.get("average_prediction", 0))

        # -------------------------------
        # ABSENCE RISK
        # -------------------------------
        absence_prob = preds.get("absence_likelihood", 1 - tomorrow_val)
        if absence_prob > 0.40:
            risk = "high"
        elif absence_prob > 0.25:
            risk = "medium"
        else:
            risk = "low"

        # -------------------------------
        # REAL STREAK FORECAST (DICT)
        # -------------------------------
        streak = predictor.calculate_streak_forecast(
            df=predictor.load_data(),
            tomorrow_pred=tomorrow_val
        )

        # -------------------------------
        # FINAL JSON RESPONSE
        # -------------------------------
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
                    "current_streak": streak.get("current_streak", 0),
                    "probability_continue": streak.get("probability_continue", 0),
                    "expected_end_in": streak.get("expected_end_in", 0)
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
