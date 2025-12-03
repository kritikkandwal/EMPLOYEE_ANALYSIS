import os, json
from datetime import date, timedelta

CACHE_DIR = "data/attendance_cache/"
os.makedirs(CACHE_DIR, exist_ok=True)

def cache_path(user_id):
    return os.path.join(CACHE_DIR, f"{user_id}.json")

def load_cache(user_id):
    path = cache_path(user_id)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return {}

def save_cache(user_id, data):
    path = cache_path(user_id)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def set_day(user_id, dt, status, hours):
    """Save attendance record in cache"""
    data = load_cache(user_id)
    iso = dt.isoformat()
    data[iso] = {
        "status": status,
        "hours": hours
    }
    save_cache(user_id, data)

def get_day(user_id, dt):
    """Return day record from cache OR None"""
    data = load_cache(user_id)
    return data.get(dt.isoformat())

def ensure_history_exists(user_id, days=365):
    """
    If no history exists → create a static realistic history,
    NOT RANDOM each reload.
    """
    data = load_cache(user_id)
    if data:
        return data  # Already exists

    today = date.today()
    start = today - timedelta(days=days)

    static_data = {}
    for i in range(days):
        d = start + timedelta(days=i)
        # STATIC — same for everyone
        if d.weekday() in (5,6):  # weekend
            static_data[d.isoformat()] = {"status": "weekend", "hours": 0}
        else:
            # repeating deterministic pattern (not random)
            cycle = i % 4  
            if cycle == 0:
                static_data[d.isoformat()] = {"status": "present", "hours": 8}
            elif cycle == 1:
                static_data[d.isoformat()] = {"status": "present", "hours": 7}
            elif cycle == 2:
                static_data[d.isoformat()] = {"status": "half-day", "hours": 4}
            else:
                static_data[d.isoformat()] = {"status": "absent", "hours": 0}

    save_cache(user_id, static_data)
    return static_data
