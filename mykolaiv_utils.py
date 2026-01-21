import requests
from datetime import datetime, timedelta, timezone

BASE = "https://off.energy.mk.ua/api"

STATUS_MAP = {
    "OFF": "🔴 Світла немає",
    "SURE_OFF": "⛔ Аварійне відключення",
    "PROBABLY_OFF": "🟡 Можливе відключення",
}


# =========================================================
# 🔍 Поточний статус (Є / Немає світла)
# =========================================================
def get_current_status(queue_name: str):
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

    # 🕒 Поточний час (Київ)
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

                # ❗ PROBABLY_OFF не шлемо як повідомлення
                if code == "PROBABLY_OFF":
                    return code, None

                return code, STATUS_MAP.get(code)

    return "UNKNOWN", "🟡 Статус невизначений (можливе відключення)"


# =========================================================
# 📊 Повний графік для черги
# =========================================================
def get_schedule_for_queue(queue: str):
    try:
        queues = requests.get(
            f"{BASE}/outage-queue/by-type/3", timeout=10
        ).json()

        queue_obj = next((q for q in queues if q["name"] == queue), None)
        if not queue_obj:
            return None, "⚠️ Чергу не знайдено"

        queue_id = queue_obj["id"]

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

        lines = [f"🔌 Графік для черги {queue}:\n"]

        for sch in schedules:
            for s in sch["series"]:
                if s["outage_queue_id"] != queue_id:
                    continue

                ts = ts_map.get(s["time_series_id"])
                if not ts:
                    continue

                start, end = ts
                status = s["type"]
                lines.append(f"{start}–{end} — {status}")

        if len(lines) == 1:
            return None, "⚠️ Дані графіка тимчасово недоступні"

        return "\n".join(lines), None

    except Exception as e:
        return None, f"❌ Помилка отримання графіка: {e}"

