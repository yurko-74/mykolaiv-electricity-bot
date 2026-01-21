import requests
from datetime import datetime, timezone

BASE = "https://off.energy.mk.ua/api"

STATUS_MAP = {
    "OFF": "🔴 Світла немає",
    "SURE_OFF": "⛔ Аварійне відключення",
    "PROBABLY_OFF": "🟡 Можливе відключення",
    "ENABLE": "🟢 Є світло"
}

def get_current_status(queue_name: str):
    # 1. Отримуємо всі черги
    r = requests.get(f"{BASE}/outage-queue/by-type/3", timeout=10)
    queues = r.json()

    queue = next((q for q in queues if q["name"] == queue_name), None)
    if not queue:
        return None, f"❌ Чергу {queue_name} не знайдено"

    queue_id = queue["id"]

    # 2. Часові інтервали
    r = requests.get(f"{BASE}/schedule/time-series", timeout=10)
    time_series = {t["id"]: t for t in r.json()}

    # 3. Активний графік
    r = requests.get(f"{BASE}/v2/schedule/active", timeout=10)
    schedules = r.json()

    now = datetime.now(timezone.utc)

    for sch in schedules:
        for s in sch["series"]:
            if s["outage_queue_id"] != queue_id:
                continue

            ts = time_series.get(s["time_series_id"])
            if not ts:
                continue

            start = datetime.fromisoformat(ts["start"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(ts["end"].replace("Z", "+00:00"))

            if start <= now < end:
                status_code = s["type"]
                return status_code, STATUS_MAP.get(status_code, status_code)

    return "ENABLE", STATUS_MAP["ENABLE"]
