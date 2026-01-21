import requests
from datetime import datetime

BASE = "https://off.energy.mk.ua/api"


def parse_time(t: str) -> int:
    """HH:MM -> minutes from 00:00"""
    h, m = map(int, t.split(":"))
    return h * 60 + m


def format_time(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def group_intervals(intervals: list[tuple[int, int, str]]) -> list[str]:
    """
    (start_min, end_min, type) -> grouped text
    """
    if not intervals:
        return []

    intervals.sort()
    result = []

    cur_start, cur_end, cur_type = intervals[0]

    for start, end, typ in intervals[1:]:
        if start == cur_end and typ == cur_type:
            cur_end = end
        else:
            result.append(
                f"{format_time(cur_start)}–{format_time(cur_end)} — {cur_type}"
            )
            cur_start, cur_end, cur_type = start, end, typ

    result.append(
        f"{format_time(cur_start)}–{format_time(cur_end)} — {cur_type}"
    )

    return result


def get_schedule_for_queue(queue_name: str) -> str:
    # 1️⃣ Черги
    r = requests.get(f"{BASE}/outage-queue/by-type/3", timeout=10)
    queues = r.json()

    queue = next((q for q in queues if q["name"] == queue_name), None)
    if not queue:
        return f"❌ Чергу {queue_name} не знайдено"

    queue_id = queue["id"]

    # 2️⃣ Часові серії
    r = requests.get(f"{BASE}/schedule/time-series", timeout=10)
    time_series = {}

    for t in r.json():
        start = t["start"][:5]
        end = t["end"][:5]
        time_series[t["id"]] = (parse_time(start), parse_time(end))

    # 3️⃣ Активний графік
    r = requests.get(f"{BASE}/v2/schedule/active", timeout=10)
    schedules = r.json()

    intervals = []

    for sch in schedules:
        for s in sch["series"]:
            if s["outage_queue_id"] == queue_id:
                ts = time_series.get(s["time_series_id"])
                if ts:
                    intervals.append((ts[0], ts[1], s["type"]))

    if not intervals:
        return f"ℹ️ Для черги {queue_name} наразі немає відключень"

    grouped = group_intervals(intervals)

    text = f"🔌 Графік для черги {queue_name}:\n\n"
    text += "\n".join(grouped)
    return text
