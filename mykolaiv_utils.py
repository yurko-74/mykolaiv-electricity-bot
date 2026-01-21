import requests
from datetime import datetime, timedelta, timezone

BASE = "https://off.energy.mk.ua/api"

STATUS_MAP = {
    "OFF": "🔴 Світла немає",
    "SURE_OFF": "⛔ Аварійне відключення",
    "PROBABLY_OFF": "🟡 Можливе відключення",
}

def get_current_status(queue_name: str):
    queues = requests.get(f"{BASE}/outage-queue/by-type/3", timeout=10).json()
    queue = next((q for q in queues if q["name"] == queue_name), None)
    if not queue:
        return None, None

    queue_id = queue["id"]

    time_series = requests.get(f"{BASE}/schedule/time-series", timeout=10).json()
    ts_map = {t["id"]: (t["start"][:5], t["end"][:5]) for t in time_series}

    schedules = requests.get(f"{BASE}/v2/schedule/active", timeout=10).json()

    # ⏰ локальний час (UA ≈ UTC+2, без літнього часу врахуємо +2)
    now_local = datetime.utcnow() + timedelta(hours=2)
    now_time = now_local.strftime("%H:%M")

    for sch in schedules:
        start = datetime.fromisoformat(sch["from"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(sch["to"].replace("Z", "+00:00"))

        if not (start <= datetime.utcnow() <= end):
            continue

        for s in sch["series"]:
            if s["outage_queue_id"] != queue_id:
                continue

            ts = ts_map.get(s["time_series_id"])
            if not ts:
                continue

            ts_start, ts_end = ts

            if ts_start <= now_time < ts_end:
                code = s["type"]

                if code == "PROBABLY_OFF":
                    return code, None  # ❗ не шлемо

                return code, STATUS_MAP.get(code)

    # 👉 якщо нічого не знайшли — світло є
    return "ENABLE", "🟢 Є світло"
