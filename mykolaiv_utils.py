import requests

BASE = "https://off.energy.mk.ua/api"
TIMEOUT = 10


def get_schedule_for_queue(queue_name: str) -> str:
    # === 1. Отримуємо черги (тип 3 = ГПВ) ===
    try:
        r = requests.get(f"{BASE}/outage-queue/by-type/3", timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return f"❌ Помилка отримання черг: {e}"

    # API може повернути або список, або {"data": [...]}
    queues = data["data"] if isinstance(data, dict) and "data" in data else data

    queue = next((q for q in queues if q.get("name") == queue_name), None)
    if not queue:
        return f"❌ Чергу {queue_name} не знайдено"

    queue_id = queue["id"]

    # === 2. Часові інтервали ===
    try:
        r = requests.get(f"{BASE}/schedule/time-series", timeout=TIMEOUT)
        r.raise_for_status()
        time_series = r.json()
    except Exception as e:
        return f"❌ Помилка отримання часових інтервалів: {e}"

    times = {
        t["id"]: f'{t["start"][:5]}–{t["end"][:5]}'
        for t in time_series
    }

    # === 3. Активний графік ===
    try:
        r = requests.get(f"{BASE}/v2/schedule/active", timeout=TIMEOUT)
        r.raise_for_status()
        schedules = r.json()
    except Exception as e:
        return f"❌ Помилка отримання графіку: {e}"

    result = []

    for sch in schedules:
        for s in sch.get("series", []):
            if s.get("outage_queue_id") == queue_id:
                time = times.get(s.get("time_series_id"), "??:??")
                status = s.get("type", "UNKNOWN")
                result.append(f"{time} — {status}")

    if not result:
        return f"ℹ️ Для черги {queue_name} наразі немає відключень"

    # Сортуємо по часу
    result.sort()

    text = f"🔌 Графік для черги {queue_name}:\n\n"
    text += "\n".join(result)

    return text
