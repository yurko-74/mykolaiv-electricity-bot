import requests
from datetime import datetime

BASE = "https://off.energy.mk.ua/api"

STATUS_MAP = {
    "OFF": "🔴 Світла немає",
    "SURE_OFF": "⛔ Аварійне відключення",
    "PROBABLY_OFF": "🟡 Можливе відключення",
    "ENABLE": "🟢 Є світло",
}

def get_current_status(queue_name: str):
    # 1️⃣ черги
    queues = requests.get(f"{BASE}/outage-queue/by-type/3", timeout=10).json()
    queue = next((q for q in queues if q["name"] == queue_name), None)

    if not queue:
        return None, None

    queue_id = queue["id"]

    # 2️⃣ time-series
    time_series = requests.get(f"{BASE}/schedule/time-series", timeout=10).json()

    now = datetime.now().strftime("%H:%M")

    # 3️⃣ активний графік
    schedules = requests.get(f"{BASE}/v2/schedule/active", timeout=10).json()

    for sch in schedules:
        for s in sch["series"]:
            if s["outage_queue_id"] != queue_id:
                continue

            ts = next(t for t in time_series if t["id"] == s["time_series_id"])

            start = ts["start"][:5]   # "00:00"
            end = ts["end"][:5]       # "00:30"

            # ⏱ просте і надійне порівняння
            if start <= now < end:
                code = s["type"]
                return code, STATUS_MAP.get(code)

    return "ENABLE", STATUS_MAP["ENABLE"]
