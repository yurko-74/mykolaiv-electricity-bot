from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from mykolaiv_utils import get_schedule_for_queue
from mykolaiv_db import init_db

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
    try:
        user_id = update.effective_user.id
        queue = update.message.text.strip()

        print(f"Отримано вибір черги: {queue} від користувача {user_id}")

        if not is_allowed(user_id):
            await update.message.reply_text("Ви не маєте доступу до цього бота.")
            return

        selected = context.user_data.get("queues", [])

        if queue in selected:
            await update.message.reply_text(
                f"ℹ️ Черга {queue} вже додана."
            )
            return

        if len(selected) >= MAX_QUEUES:
            await update.message.reply_text(
                "⚠️ Можна обрати не більше двох черг.\n"
                "Якщо потрібно змінити — просто напишіть /start"
            )
            return

        selected.append(queue)
        context.user_data["queues"] = selected

        await update.message.reply_text(
            f"✅ Чергу {queue} збережено.\n"
            f"📡 Отримую графік..."
        )

        schedule = get_schedule_for_queue(queue)

        print(f"Результат schedule: {schedule}")

        await update.message.reply_text(schedule)

        if len(selected) == 1:
            await update.message.reply_text(
                "ℹ️ За потреби ви можете обрати **ще одну чергу**.\n"
                "Або нічого не робіть — я буду надсилати інформацію для цієї.",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "✅ Обрано дві черги.\n"
                "ℹ️ Для зміни вибору введіть /start"
            )

    except Exception as e:
        error_text = f"Сталася помилка: {str(e)}"
        print(error_text)
        await update.message.reply_text(error_text)



def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_queue))

    print("Бот запущений...")
    init_db()
    app.run_polling()

if __name__ == "__main__":
    main()







