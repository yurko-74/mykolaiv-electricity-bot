import requests

URL = "https://off.energy.mk.ua/"

def get_schedule_for_queue(queue):
    try:
        response = requests.get(URL, timeout=10)
        text = response.text

        # Поки робимо просту заглушку:
        return f"Графік для черги {queue} буде тут.\n(Інтеграція з сайтом на наступному кроці)"

    except Exception as e:
        return f"Помилка отримання даних: {e}"
