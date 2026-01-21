from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from mykolaiv_utils import get_current_status
from mykolaiv_db import (
    init_db,
    add_user,
    is_allowed,
)

import os


TOKEN = os.getenv("BOT_TOKEN")
MAX_QUEUES = 2

KEYBOARD = [
    ["1.1", "1.2"],
    ["2.1", "2.2"],
    ["3.1", "3.2"],
    ["4.1", "4.2"],
    ["5.1", "5.2"],
    ["6.1", "6.2"],
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id)

    context.user_data.clear()

    await update.message.reply_text(
        "Вітаю! Оберіть свій код черги для м. Миколаїв:",
        reply_markup=ReplyKeyboardMarkup(KEYBOARD, resize_keyboard=True),
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
            await update.message.reply_text(f"ℹ️ Черга {queue} вже додана.")
            return

        if len(selected) >= MAX_QUEUES:
            await update.message.reply_text(
                "⚠️ Можна обрати не більше двох черг.\n"
                "Для зміни введіть /start"
            )
            return

        # ✅ зберігаємо вибір
        selected.append(queue)
        context.user_data["queues"] = selected

        # ✅ показуємо ТІЛЬКИ поточний статус
        status_code, status_text = get_current_status(queue)

        if status_text:
            await update.message.reply_text(
                f"{status_text}\nЧерга {queue}"
            )

        if len(selected) == 1:
            await update.message.reply_text(
                "ℹ️ За потреби ви можете обрати **ще одну чергу**.\n"
                "Або нічого не робіть — я повідомлятиму лише про зміни.",
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text(
                "✅ Обрано дві черги.\nℹ️ Для зміни вибору введіть /start"
            )

    except Exception as e:
        print(e)
        await update.message.reply_text(f"❌ Помилка: {e}")


async def check_updates(context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    users_data = context.bot_data.get("users", {})

    for user_id, data in users_data.items():
        queues = data.get("queues", [])
        last_status = data.get("last_status", {})

        for queue in queues:
            status_code, status_text = get_current_status(queue)

            if status_code is None:
                continue

            if last_status.get(queue) == status_code:
                continue

            if status_code == "PROBABLY_OFF":
                last_status[queue] = status_code
                continue

            await bot.send_message(
                chat_id=user_id,
                text=f"{status_text}\nЧерга {queue}"
            )

            last_status[queue] = status_code

        data["last_status"] = last_status



def main():
    init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_queue))

    # ❗ тільки якщо встановлено job-queue
    app.job_queue.run_repeating(check_updates, interval=300, first=20)

    print("🤖 Бот запущений")
    app.run_polling()



if __name__ == "__main__":
    main()




