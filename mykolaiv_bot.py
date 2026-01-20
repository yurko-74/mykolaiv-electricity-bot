from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from mykolaiv_utils import get_schedule_for_queue
from mykolaiv_db import add_user, is_allowed

import os
TOKEN = os.getenv("BOT_TOKEN")

KEYBOARD = [
    ["1.1", "1.2"],
    ["2.1", "2.2"],
    ["3.1", "3.2"],
    ["4.1", "4.2"],
    ["5.1", "5.2"],
    ["6.1", "6.2"]
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id)

    await update.message.reply_text(
        "Вітаю! Оберіть свій код черги для м. Миколаїв:",
        reply_markup=ReplyKeyboardMarkup(KEYBOARD, resize_keyboard=True)
    )

async def handle_queue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_allowed(user_id):
        await update.message.reply_text("Ви не маєте доступу до цього бота.")
        return

   queue = update.message.text.strip()

    await update.message.reply_text(f"Отримав запит для черги: {queue}. Збираю дані...")

    schedule = get_schedule_for_queue(queue)

    await update.message.reply_text(schedule)


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_queue))

    print("Бот запущений...")
    app.run_polling()

if __name__ == "__main__":
    main()



