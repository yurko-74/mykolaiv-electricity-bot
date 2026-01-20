import requests

API_URL = "https://off.energy.mk.ua/api/schedule/queue"

STATUS_MAP = {
    "ENABLE": "Є світло",
    "OFF": "Заплановане відключення",
    "SURE_OFF": "Актуальне відключення",
    "PROBABLY_OFF": "Можливе відключення"
}

def get_schedule_for_queue(queue):
    try:
        response = requests.get(API_URL, timeout=10)

        print("STATUS CODE:", response.status_code)
        print("RESPONSE TEXT:", response.text[:500])

        if response.status_code != 200:
            return f"API повернув статус {response.status_code}"

        data = response.json()

        print("PARSED JSON:", data)

        if not data:
            return "API повернув порожні дані"

        # можливо дані лежать в іншому полі
        schedule_rows = data.get("data") or data

        if not schedule_rows:
            return f"Немає поля 'data' в API. Ключі: {list(data.keys())}"

        report_lines = [f"📅 Графік на сьогодні для черги {queue}:\n"]

        for row in schedule_rows:
            time = row.get("time")
            queue_info = row.get(queue)

            if not time or not queue_info:
                continue

            status_key = queue_info.get("type", "")
            status_text = STATUS_MAP.get(status_key, status_key)

            report_lines.append(f"{time} — {status_text}")

        if len(report_lines) == 1:
            return f"Дані для черги {queue} відсутні в отриманому JSON"

        return "\n".join(report_lines)

    except Exception as e:
        return f"Помилка при отриманні даних: {e}"


