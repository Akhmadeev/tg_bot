import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from config import TELEGRAM_TOKEN, CHAT_ID
from scanner import find_signals

# Команда /start
async def start(update, context):
    keyboard = [[InlineKeyboardButton("🔥 Найти точку входа", callback_data="entry_point")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

# Обработка нажатий кнопок
async def button_handler(update, context):
    query = update.callback_query
    await query.answer()

    if query.data == "entry_point":
        await query.edit_message_text("⏳ Ищу волатильные монеты...")
        await find_signals(context.bot, chat_id=query.message.chat_id)

# Периодический анализ
async def scheduled_scanner(bot):
    while True:
        await find_signals(bot)
        await asyncio.sleep(300)  # каждые 5 минут

# Основной запуск бота
async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.create_task(scheduled_scanner(app.bot))

    print("✅ Бот запущен.")
    await app.run_polling()