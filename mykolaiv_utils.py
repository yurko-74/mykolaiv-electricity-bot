import requests
from bs4 import BeautifulSoup
from datetime import datetime

URL = "https://off.energy.mk.ua/"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# кольори, які означають ВІДКЛЮЧЕННЯ
OFF_COLORS = ["#ff4d4d", "#ff9999", "red"]

def get_schedule_for_queue(queue: str) -> str:
    try:
        response = requests.get(URL, headers=HEADERS, timeout=20)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        table = soup.find("table")
        if not table:
            return "❌ Не знайдено таблицю графіка"

        headers = table.find("thead").find_all("th")
        queue_index = None

        for i, th in enumerate(headers):
            if queue in th.get_text(strip=True):
                queue_index = i
                break

        if queue_index is None:
            return f"❌ Чергу {queue} не знайдено"

        now = datetime.now().time()
        off_periods = []

        for row in table.find("tbody").find_all("tr"):
            cells = row.find_all("td")
            if len(cells) <= queue_index:
                continue

            time_text = cells[0].get_text(strip=True)
            try:
                row_time = datetime.strptime(time_text, "%H:%M").time()
            except ValueError:
                continue

            if row_time < now:
                continue

            cell = cells[queue_index]
            style = cell.get("style", "").lower()

            if any(color in style for color in OFF_COLORS):
                off_periods.append(time_text)

        if not off_periods:
            return f"✅ Для черги {queue} до кінця доби відключень не заплановано"

        result = f"⚡ Відключення для черги {queue}:\n\n"
        result += "\n".join(off_periods)

        return result

    except Exception as e:
        return f"❌ Помилка: {e}"
