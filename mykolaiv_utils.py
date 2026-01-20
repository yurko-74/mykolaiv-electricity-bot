import requests

API_URL = "https://off.energy.mk.ua/api/schedule/time-series"

# Переклад типів у зручний текст
STATUS_MAP = {
    "ENABLE": "Є світло",
    "OFF": "Заплановане відключення",
    "SURE_OFF": "Актуальне відключення",
    "PROBABLY_OFF": "Можливе відключення"
}

def get_schedule_for_queue(queue):
    try:
        response = requests.get(API_URL, timeout=10)
        data = response.json()

        # Перевіряємо, чи є потрібна черга
        if not data or "data" not in data:
            return "Неможливо отримати дані з API"

        schedule_rows = data["data"]
        
        # Формуємо текстовий графік
        report_lines = []
        report_lines.append(f"📅 Графік на сьогодні для черги {queue}:\n")

        for row in schedule_rows:
            time = row.get("time", "??:??")
            queue_info = row.get(queue)

            if not queue_info:
                continue

            status_key = queue_info.get("type", "")
            status_text = STATUS_MAP.get(status_key, status_key)

            report_lines.append(f"{time} — {status_text}")

        # Якщо нічого не знайдено
        if len(report_lines) <= 1:
            return f"Дані для черги {queue} не знайдено."

        return "\n".join(report_lines)

    except Exception as e:
        return f"Помилка при отриманні даних: {e}"

