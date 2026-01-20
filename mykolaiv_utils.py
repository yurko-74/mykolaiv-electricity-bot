import requests

URL = "https://off.energy.mk.ua/"

def get_schedule_for_queue(queue):
    try:
        response = requests.get(URL, timeout=10)

        if response.status_code != 200:
            return f"Помилка сайту: статус {response.status_code}"

        text = response.text

        return f"Дані з сайту отримано успішно для черги {queue}.\nДовжина відповіді: {len(text)} символів"

    except Exception as e:
        return f"Помилка отримання даних: {e}"
