# analytics_store.py
import json
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, Optional

from flask import Blueprint, jsonify, request

# ============================================================
# PATHS & CONSTANTS
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

STORE_PATH = DATA_DIR / "analytics_store.json"

analytics_store_bp = Blueprint("analytics_store", __name__, url_prefix="/api/storage")


# ============================================================
# DEFAULT STRUCTURE
# ============================================================
def _today_str() -> str:
    return date.today().strftime("%Y-%m-%d")


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def get_default_structure() -> Dict[str, Any]:
    """
    Base JSON structure for analytics_store.json.
    You can tweak field names here if your logic changes.
    """
    return {
        "date": _today_str(),
        "attendance": {
            "status_today": "",           # "present" / "absent" / "half-day" etc.
            "prediction": "",             # e.g., "high probability of present"
            "absence_likelihood": "",     # e.g., "low", "medium", "high"
            "trend": []                   # list of historical / predicted values
        },
        "productivity": {
            "score_today": 0,             # numeric score 0–100
            "prediction": "",             # e.g., "high", "medium", "low"
            "trend": []                   # historical/predicted productivity scores
        },
        "tasks": {
            "completed_today": 0,
            "total_today": 0,
            "completion_ratio": 0.0,      # completed_today / total_today
            "task_prediction": ""         # e.g., "on-track", "behind", etc.
        },
        "meta": {
            "employee_id": "",            # optional, can be static for single-user system
            "last_update": _now_iso(),    # last time store was written
            "notes": ""                   # any extra info
        }
    }


# ============================================================
# CORE FILE OPS
# ============================================================
def initialize_storage(force_reset: bool = False) -> Dict[str, Any]:
    """
    Ensure analytics_store.json exists and is valid.
    If force_reset=True, recreate from default.
    Returns the loaded/created structure.
    """
    if force_reset or not STORE_PATH.exists():
        data = get_default_structure()
        save_data(data)
        return data

    try:
        with STORE_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        # Corruption or read error → reset to default
        data = get_default_structure()
        save_data(data)
        return data

    # Repair missing keys / sections
    default = get_default_structure()
    repaired = _merge_with_default(data, default)
    if repaired != data:
        save_data(repaired)
    return repaired


def _merge_with_default(current: Dict[str, Any], default: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge current data with default structure.
    Ensures missing keys are added without wiping existing content.
    """
    if not isinstance(current, dict) or not isinstance(default, dict):
        return current

    merged = dict(current)
    for key, def_val in default.items():
        if key not in merged:
            merged[key] = def_val
        else:
            if isinstance(def_val, dict) and isinstance(merged[key], dict):
                merged[key] = _merge_with_default(merged[key], def_val)
    return merged


def load_data() -> Dict[str, Any]:
    """
    Safe read. Always returns a valid structure.
    """
    return initialize_storage(force_reset=False)


def save_data(data: Dict[str, Any]) -> None:
    """
    Overwrite entire JSON file. Also updates meta.last_update and date.
    """
    if not isinstance(data, dict):
        raise ValueError("data must be a dict")

    # Ensure base structure & keys
    default = get_default_structure()
    merged = _merge_with_default(data, default)

    # Auto-update date + meta.last_update
    merged["date"] = _today_str()
    if "meta" not in merged or not isinstance(merged["meta"], dict):
        merged["meta"] = default["meta"]
    merged["meta"]["last_update"] = _now_iso()

    with STORE_PATH.open("w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)


# ============================================================
# SECTION HELPERS
# ============================================================
def update_section(section: str, key: str, value: Any) -> Dict[str, Any]:
    """
    Update a single key inside a top-level section.
    e.g., update_section("attendance", "prediction", "High")
    """
    data = load_data()

    if section not in data or not isinstance(data[section], dict):
        # if section missing, initialize with default for that section
        default = get_default_structure()
        data[section] = default.get(section, {})

    data[section][key] = value
    save_data(data)
    return data


def update_whole_section(section: str, dict_value: Dict[str, Any]) -> Dict[str, Any]:
    """
    Replace/merge an entire section.
    Example:
        update_whole_section("productivity", {
            "score_today": 82,
            "prediction": "High",
            "trend": [60, 70, 82]
        })
    """
    if not isinstance(dict_value, dict):
        raise ValueError("dict_value must be a dict")

    data = load_data()

    # Merge with default for that section to keep structure stable
    default = get_default_structure()
    section_default = default.get(section, {})

    if section not in data or not isinstance(data[section], dict):
        data[section] = section_default

    # Shallow merge
    new_section = dict(data[section])
    new_section.update(dict_value)
    data[section] = new_section

    save_data(data)
    return data


# ============================================================
# FLASK ROUTES
# ============================================================

@analytics_store_bp.route("/get", methods=["GET"])
def api_get_storage():
    """
    GET /api/storage/get
    Returns the full analytics_store.json content.
    """
    data = load_data()
    return jsonify({"success": True, "data": data})


@analytics_store_bp.route("/set", methods=["POST"])
def api_set_storage():
    """
    POST /api/storage/set
    Completely replace analytics_store.json content.
    Body: JSON object matching the store structure.
    """
    try:
        incoming = request.get_json(force=True, silent=False)
        if not isinstance(incoming, dict):
            return jsonify({"success": False, "error": "Body must be a JSON object"}), 400

        save_data(incoming)
        return jsonify({"success": True, "data": load_data()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@analytics_store_bp.route("/update", methods=["PATCH", "POST"])
def api_update_storage():
    """
    PATCH/POST /api/storage/update

    Accepts two patterns:

    1) Single key inside section:
       {
         "section": "attendance",
         "key": "prediction",
         "value": "High"
       }

    2) Whole section update:
       {
         "section": "productivity",
         "data": {
           "score_today": 80,
           "prediction": "Medium",
           "trend": [70, 75, 80]
         }
       }
    """
    body = request.get_json(force=True, silent=True) or {}
    section = body.get("section")

    if not section:
        return jsonify({"success": False, "error": "Missing 'section' field"}), 400

    # Case 1: single key
    key = body.get("key")
    if key is not None and "value" in body:
        value = body["value"]
        try:
            data = update_section(section, key, value)
            return jsonify({"success": True, "data": data})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    # Case 2: section data
    if "data" in body and isinstance(body["data"], dict):
        dict_value = body["data"]
        try:
            data = update_whole_section(section, dict_value)
            return jsonify({"success": True, "data": data})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    return jsonify({
        "success": False,
        "error": "Provide either ('key' + 'value') or a dict 'data' to update section."
    }), 400


@analytics_store_bp.route("/reset", methods=["POST"])
def api_reset_storage():
    """
    POST /api/storage/reset
    Resets analytics_store.json back to default structure.
    """
    try:
        data = initialize_storage(force_reset=True)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# OPTIONAL: direct run for debugging
# ============================================================
if __name__ == "__main__":
    from flask import Flask

    app = Flask(__name__)
    app.register_blueprint(analytics_store_bp)

    @app.route("/")
    def index():
        return "analytics_store.py standalone test server"

    app.run(debug=True)
