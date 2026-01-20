import requests

URL = "https://off.energy.mk.ua/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
}

def get_schedule_for_queue(queue):
    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)

        if response.status_code != 200:
            return f"Помилка сайту: статус {response.status_code}"

        text = response.text

        return f"Дані з сайту отримано успішно для черги {queue}. Довжина: {len(text)}"

    except Exception as e:
        return f"Помилка отримання даних: {e}"
