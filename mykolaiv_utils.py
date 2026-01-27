import requests
from datetime import datetime, timedelta, timezone

BASE = "https://off.energy.mk.ua/api"

STATUS_MAP = {
    "OFF": "🔴 Світла немає",
    "SURE_OFF": "⛔ Аварійне відключення",
    "PROBABLY_OFF": "⚠️ За графіком можливе відключення",
    "ENABLE": "🟢 Є світло",
}


def get_current_status(queue_name: str):
    try:
        queues = requests.get(
            f"{BASE}/outage-queue/by-type/3", timeout=10
        ).json()

        queue = next((q for q in queues if q["name"] == queue_name), None)
        if not queue:
            return None, None

        queue_id = queue["id"]

        time_series = requests.get(
            f"{BASE}/schedule/time-series", timeout=10
        ).json()

        ts_map = {
            t["id"]: (t["start"][:5], t["end"][:5])
            for t in time_series
        }

        schedules = requests.get(
            f"{BASE}/v2/schedule/active", timeout=10
        ).json()

        now_utc = datetime.now(timezone.utc)
        now_local = now_utc.astimezone(timezone(timedelta(hours=2)))
        now_time = now_local.strftime("%H:%M")

        for sch in schedules:
            start = datetime.fromisoformat(sch["from"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(sch["to"].replace("Z", "+00:00"))

            if not (start <= now_utc <= end):
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
                    return code, STATUS_MAP.get(code)

        return "ENABLE", STATUS_MAP["ENABLE"]

    except Exception:
        return None, None


# 🆕 НОВА ФУНКЦІЯ
def get_day_schedule(queue_name: str, start="05:00", end="23:59"):
    """
    Повертає список об'єднаних періодів:
    [
        ("05:00", "07:30", "🔴 Світла немає"),
        ("07:30", "11:00", "🟢 Є світло"),
        ...
    ]
    """
    try:
        queues = requests.get(
            f"{BASE}/outage-queue/by-type/3", timeout=10
        ).json()

        queue = next((q for q in queues if q["name"] == queue_name), None)
        if not queue:
            return []

        queue_id = queue["id"]

        time_series = requests.get(
            f"{BASE}/schedule/time-series", timeout=10
        ).json()

        ts_map = {
            t["id"]: (t["start"][:5], t["end"][:5])
            for t in time_series
        }

        schedules = requests.get(
            f"{BASE}/v2/schedule/active", timeout=10
        ).json()

        day_slots = []

        for sch in schedules:
            for s in sch["series"]:
                if s["outage_queue_id"] != queue_id:
                    continue

                ts = ts_map.get(s["time_series_id"])
                if not ts:
                    continue

                ts_start, ts_end = ts

                if ts_end <= start or ts_start >= end:
                    continue

                slot_start = max(ts_start, start)
                slot_end = min(ts_end, end)

                status = STATUS_MAP.get(s["type"], "❓ Невідомо")
                day_slots.append((slot_start, slot_end, status))

        if not day_slots:
            return [(start, end, STATUS_MAP["ENABLE"])]

        # 🔗 об'єднання суміжних інтервалів
        day_slots.sort()
        merged = [day_slots[0]]

        for cur_start, cur_end, cur_status in day_slots[1:]:
            last_start, last_end, last_status = merged[-1]

            if cur_start == last_end and cur_status == last_status:
                merged[-1] = (last_start, cur_end, last_status)
            else:
                merged.append((cur_start, cur_end, cur_status))

        return merged

    except Exception:
        return []
