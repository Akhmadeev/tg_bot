import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import TELEGRAM_TOKEN
from scanner import find_signals

# 🔁 Периодический запуск анализа
async def scheduled_scanner(app):
    while True:
        await find_signals(app.bot)
        await asyncio.sleep(300)

# 📲 Команда /start
async def start(update, context):
    keyboard = [
        [InlineKeyboardButton("🔥 Найти точку входа", callback_data="entry_point")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

# 🔘 Обработка нажатий кнопок
async def button_handler(update, context):
    query = update.callback_query
    await query.answer()

    if query.data == "entry_point":
        await query.edit_message_text("⏳ Ищу волатильные монеты...")
        await find_signals(context.bot, chat_id=query.message.chat_id)

# 🧠 Основная функция
async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    # запускаем фоновую задачу
    app.create_task(scheduled_scanner(app))

    print("✅ Бот запущен.")
    await app.run_polling()

# Для run_forever.py
def run_bot():
    asyncio.run(main())
