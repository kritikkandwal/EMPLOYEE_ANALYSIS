import os, json, threading
from flask import Blueprint, jsonify, request
from flask_login import login_required

predictions_bp = Blueprint("predictions_bp", __name__)

PREDICTION_DIR = "data/predictions"
PREDICTION_FILE = f"{PREDICTION_DIR}/prediction_store.json"

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
