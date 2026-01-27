import requests
from datetime import datetime, timedelta, timezone

BASE = "https://off.energy.mk.ua/api"

STATUS_MAP = {
    "OFF": "🔴 Світла немає",
    "SURE_OFF": "⛔ Аварійне відключення",
    "PROBABLY_OFF": "⚠️ За графіком можливе відключення",
    "ENABLE": "🟢 Є світло",
}

# 🔥 КЕШ
_CACHE = {
    "queues": {"data": None, "ts": None},
    "time_series": {"data": None, "ts": None},
    "schedule": {"data": None, "ts": None},
}

CACHE_TTL = timedelta(minutes=15)


def _cached_get(key: str, url: str):
    now = datetime.utcnow()

    entry = _CACHE[key]
    if entry["data"] and entry["ts"] and now - entry["ts"] < CACHE_TTL:
        return entry["data"]

    resp = requests.get(url, timeout=10).json()
    entry["data"] = resp
    entry["ts"] = now
    return resp


def _get_base_data():
    queues = _cached_get("queues", f"{BASE}/outage-queue/by-type/3")
    time_series = _cached_get("time_series", f"{BASE}/schedule/time-series")
    schedules = _cached_get("schedule", f"{BASE}/v2/schedule/active")
    return queues, time_series, schedules


def get_current_status(queue_name: str):
    try:
        queues, time_series, schedules = _get_base_data()

        queue = next((q for q in queues if q["name"] == queue_name), None)
        if not queue:
            return None, None

        queue_id = queue["id"]

        ts_map = {
            t["id"]: (t["start"][:5], t["end"][:5])
            for t in time_series
        }

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


def get_day_schedule(queue_name: str, start="05:00", end="23:59"):
    try:
        queues, time_series, schedules = _get_base_data()

        queue = next((q for q in queues if q["name"] == queue_name), None)
        if not queue:
            return []

        queue_id = queue["id"]

        ts_map = {
            t["id"]: (t["start"][:5], t["end"][:5])
            for t in time_series
        }

        slots = []

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

                slots.append(
                    (slot_start, slot_end, STATUS_MAP.get(s["type"], "❓"))
                )

        if not slots:
            return [(start, end, STATUS_MAP["ENABLE"])]

        slots.sort()
        merged = [slots[0]]

        for cur_start, cur_end, cur_status in slots[1:]:
            last_start, last_end, last_status = merged[-1]
            if cur_start == last_end and cur_status == last_status:
                merged[-1] = (last_start, cur_end, last_status)
            else:
                merged.append((cur_start, cur_end, cur_status))

        return merged

    except Exception:
        return []
