import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from config import TELEGRAM_TOKEN, CHAT_ID
from scanner import find_signals, find_news_with_volume_spike
from ai_comment import comment_on

# Главное меню
main_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔥 Найти точку входа", callback_data="entry_point")],
    [InlineKeyboardButton("📰 Новости + Объем", callback_data="news_volume")],
    [InlineKeyboardButton("🎮 Заглушка 1", callback_data="stub_1")],
    [InlineKeyboardButton("🚫 Заглушка 2", callback_data="stub_2")],
])

# Команда /start
async def start(update, context):
    if update.message:
        await update.message.reply_text("Выберите действие:", reply_markup=main_keyboard)

# Обработка нажатий кнопок
async def button_handler(update, context):
    query = update.callback_query
    await query.answer()

    if query.data == "entry_point":
        await query.edit_message_text("🔄 Расчет точки входа...", reply_markup=main_keyboard)
        await find_signals(context.bot, chat_id=query.message.chat_id)
    elif query.data == "news_volume":
        await query.edit_message_text("🔄 Получение новостей и анализа...", reply_markup=main_keyboard)
        await find_news_with_volume_spike(context.bot, chat_id=query.message.chat_id)
    elif query.data.startswith("stub"):
        await query.edit_message_text("🚫 Функция в разработке", reply_markup=main_keyboard)
    elif query.data.startswith("ai_comment"):
        _, symbol, rsi, volume = query.data.split("|")
        ai = comment_on(symbol, float(rsi), float(volume))
        msg = f"🧠 AI-комментарий по {symbol}:\n{ai}"
        await context.bot.send_message(chat_id=query.message.chat_id, text=msg)

# Периодический анализ
async def scheduled_scanner(bot):
    while True:
        await find_signals(bot)
        await asyncio.sleep(300)

# Основной запуск бота
async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.create_task(scheduled_scanner(app.bot))

    print("✅ Бот запущен.")
    await app.run_polling()

# Для запуска через run_forever.py
def run_bot():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        print("⚠️ Event loop уже запущен. Использую create_task.")
        loop.create_task(main())
    else:
        asyncio.run(main())
