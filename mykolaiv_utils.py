import requests

BASE = "https://off.energy.mk.ua/api"

def get_schedule_for_queue(queue_name: str) -> str:
    # 1. Отримуємо всі черги
    r = requests.get(f"{BASE}/outage-queue/by-type/3", timeout=10)
    queues = r.json()

    queue = next((q for q in queues if q["name"] == queue_name), None)
    if not queue:
        return f"❌ Чергу {queue_name} не знайдено"

    queue_id = queue["id"]

    # 2. Часові інтервали
    r = requests.get(f"{BASE}/schedule/time-series", timeout=10)
    times = {t["id"]: f'{t["start"][:5]}–{t["end"][:5]}' for t in r.json()}

    # 3. Активний графік
    r = requests.get(f"{BASE}/v2/schedule/active", timeout=10)
    schedules = r.json()

    result = []

    for sch in schedules:
        for s in sch["series"]:
            if s["outage_queue_id"] == queue_id:
                time = times.get(s["time_series_id"], "??")
                result.append(f"{time} — {s['type']}")

    if not result:
        return f"ℹ️ Для черги {queue_name} наразі немає відключень"

    text = f"🔌 Графік для черги {queue_name}:\n\n"
    text += "\n".join(sorted(result))
    return text
