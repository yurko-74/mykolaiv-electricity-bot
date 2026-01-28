from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from datetime import datetime, time

from mykolaiv_utils import get_current_status, get_day_schedule
from mykolaiv_db import init_db, add_user, is_allowed

import os

TOKEN = os.getenv("BOT_TOKEN")

KEYBOARD = [
    ["1.1", "1.2"],
    ["2.1", "2.2"],
    ["3.1", "3.2"],
    ["4.1", "4.2"],
    ["5.1", "5.2"],
    ["6.1", "6.2"],
]


def format_day_table(periods: list) -> str:
    """
    periods = [
        ("05:00", "07:30", "🟥 Відключено"),
        ("07:30", "11:00", "🟩 Є світло"),
        ...
    ]
    """
    lines = [
        "📊 *Графік на сьогодні*",
        "",
        "| Період | Статус |",
        "|--------|--------|",
    ]

    for start, end, status in periods:
        lines.append(f"| {start} – {end} | {status} |")

    return "\n".join(lines)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id)
    context.user_data.clear()

    await update.message.reply_text(
        "Вітаю! Оберіть свою чергу для м. Миколаїв:",
        reply_markup=ReplyKeyboardMarkup(KEYBOARD, resize_keyboard=True),
    )


async def handle_queue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    queue = update.message.text.strip()

    if not is_allowed(user_id):
        await update.message.reply_text("⛔ Доступ обмежено")
        return

    subs = context.bot_data.setdefault("subscriptions", {})
    user_queues = subs.setdefault(user_id, set())

    is_first = len(user_queues) == 0
    user_queues.add(queue)

    await update.message.reply_text(f"✅ Черга {queue} додана.")

    if is_first:
        await update.message.reply_text(
            "ℹ️ За потреби ви можете обрати ще одну чергу.\n"
            "Або нічого не робіть — я повідомлятиму лише про зміни."
        )


async def morning_report(context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    subs = context.bot_data.get("subscriptions", {})

    for user_id, queues in subs.items():
        for queue in queues:
            periods = get_day_schedule(queue, start="05:00", end="23:59")

            if not periods:
                continue

            table = format_day_table(periods)

            await bot.send_message(
                chat_id=user_id,
                text=f"{table}\n\nЧерга {queue}",
                parse_mode="Markdown"
            )


async def check_updates(context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    subs = context.bot_data.get("subscriptions", {})
    last = context.bot_data.setdefault("last_status", {})

    for user_id, queues in subs.items():
        user_last = last.setdefault(user_id, {})

        for queue in queues:
            status_code, status_text = get_current_status(queue)

            if not status_code:
                continue

            if user_last.get(queue) == status_code:
                continue

            await bot.send_message(
                chat_id=user_id,
                text=f"{status_text}\nЧерга {queue}"
            )

            user_last[queue] = status_code


def main():
    init_db()

    app = (
        Application.builder().token(TOKEN).timezone(timezone("Europe/Kyiv")).build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_queue))

    # 🔁 Перевірка змін кожні 20 хв
    app.job_queue.run_repeating(
        check_updates,
        interval=1200,
        first=60
    )

    # 🌅 Ранковий звіт о 05:00
    app.job_queue.run_daily(
        morning_report,
        time=time(hour=5, minute=0)
    )

    print("🤖 Бот запущений")
    app.run_polling()


if __name__ == "__main__":
    main()


