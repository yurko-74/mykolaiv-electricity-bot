from mykolaiv_db import get_all_users
from mykolaiv_utils import get_schedule_for_queue
import telegram

TOKEN = "8221410645:AAEwCG0hqjKasHSSaX52j0QU7owvlSLN1FA"

async def send_daily():
    bot = telegram.Bot(TOKEN)

    for user_id in get_all_users():
        message = get_schedule_for_queue("1.1")
        await bot.send_message(chat_id=user_id, text=message)
