import os, json, threading
from flask import Blueprint, jsonify, request
from flask_login import login_required
from flask import Blueprint, jsonify, request
from analytics_store import update_whole_section
from ml_models.productivity_forecaster import ProductivityForecaster
from flask import request

predictions_bp = Blueprint("predictions_bp", __name__)
productivity_bp = Blueprint("productivity", __name__, url_prefix="/api/productivity")
PREDICTION_DIR = "data/predictions"
PREDICTION_FILE = f"{PREDICTION_DIR}/prediction_store.json"
forecaster = ProductivityForecaster()
DEFAULT_TEMPLATE = {
    "date": None,
    "attendance": {
        "today_status": "",
        "prediction": "",
        "absence_likelihood": "",
        "trend": []
    },
    "task": {
        "completed": 0,
        "total": 0,
        "completion_ratio": 0.0,
        "task_prediction": ""
    },
    "productivity": {
        "score_today": "",
        "trend": []
    }
}

_lock = threading.Lock()


def _ensure_file():
    os.makedirs(PREDICTION_DIR, exist_ok=True)
    if not os.path.exists(PREDICTION_FILE):
        with _lock:
            with open(PREDICTION_FILE, "w") as f:
                import datetime
                tpl = DEFAULT_TEMPLATE.copy()
                tpl["date"] = datetime.date.today().isoformat()
                json.dump(tpl, f, indent=2)


def load_store():
    _ensure_file()
    with _lock:
        with open(PREDICTION_FILE, "r") as f:
            return json.load(f)


def save_store(data):
    import datetime
    data["date"] = datetime.date.today().isoformat()
    with _lock:
        with open(PREDICTION_FILE, "w") as f:
            json.dump(data, f, indent=2)


def update_section(section, key, value):
    data = load_store()

    if section not in data:
        data[section] = DEFAULT_TEMPLATE[section]

    if key is None:
        data[section] = value
    else:
        data[section][key] = value

    save_store(data)
    return data


@predictions_bp.route("/api/predictions/get")
@login_required
def api_get():
    return jsonify({"success": True, "data": load_store()})


@predictions_bp.route("/api/predictions/set", methods=["POST"])
@login_required
def api_set():
    payload = request.get_json() or {}
    save_store(payload)
    return jsonify({"success": True, "data": payload})


@predictions_bp.route("/api/predictions/update", methods=["POST"])
@login_required
def api_update():
    p = request.get_json() or {}
    section = p.get("section")
    key = p.get("key")
    value = p.get("value")

    updated = update_section(section, key, value)
    return jsonify({"success": True, "data": updated})

# =====================================================================
#   PRODUCTIVITY PREDICTION ENDPOINT
# =====================================================================
@productivity_bp.route("/predict", methods=["GET"])
def predict_productivity():
    """
    1. Runs ML prediction from ProductivityForecaster
    2. Maps result → analytics_store.json (score_today, prediction, trend)
    3. Returns full detailed AI prediction to frontend
    """

    # --- (A) INPUTS (optional from frontend) ---
    user_id = 1  # You can make this dynamic later
    today_score = request.args.get("today_score", type=float)
    completed = request.args.get("completed", type=int)
    total = request.args.get("total", type=int)

    # --- (B) RUN YOUR MAIN ML MODEL ---
    result = forecaster.get_prediction_summary(
        user_id=user_id,
        today_score=today_score,
        completed=completed,
        total=total
    )

    # ----------------------------------------------------
    # SAVE INTO analytics_store.json
    # ----------------------------------------------------
    def level(score):
        if score is None:
            return "unknown"
        s = int(score)
        if s >= 80:
            return "high"
        elif s >= 50:
            return "medium"
        else:
            return "low"

    productivity_section = {
        "score_today": int(result["tomorrow_score"]) if result["tomorrow_score"] is not None else 0,
        "prediction": level(result["tomorrow_score"]),
        "trend": result.get("next_7_days", [])
    }

    update_whole_section("productivity", productivity_section)


    

    # --- (E) RETURN FULL RESULT TO FRONTEND ---
    return jsonify({
        "success": True,
        "predictions": result
    })
    
# =====================================================================
#   UPDATE TASKS → Save into analytics_store.json
# =====================================================================

@predictions_bp.route("/api/update-productivity", methods=["POST"])
def update_productivity():
    import datetime
    from data.productivity.csv_writer import update_csv_for_day

    data = request.get_json() or {}

    date = data.get("date")
    completed = int(data.get("completed", 0))
    total = int(data.get("total", 0))

    if not date:
        date = datetime.date.today().isoformat()

    # Calculate score + write CSV
    score = update_csv_for_day(date, completed, total)

    # Save to analytics_store.json
    update_whole_section("productivity", {
        "score_today": score,
        "completed_today": completed,
        "total_today": total
    })

    return {"success": True, "saved": True, "score": score}


@productivity_bp.route("/yearly_csv")
def yearly_from_csv():
    import csv

    records = {}

    try:
        with open("data/productivity/productivity_daily.csv", "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                date = row["date"]
                score = int(row["score"])
                completed = int(row["completed"])
                total = int(row["total"])

                level = (
                    "HIGH" if score >= 80 else
                    "MEDIUM" if score >= 40 else
                    "LOW"
                )

                records[date] = {
                    "score": score,
                    "completed": completed,
                    "total": total,
                    "level": level
                }
    except FileNotFoundError:
        pass

    return {"success": True, "records": records}
