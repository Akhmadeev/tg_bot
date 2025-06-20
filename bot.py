import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from config import TELEGRAM_TOKEN, CHAT_ID
from scanner import find_signals, find_news_with_volume_spike
from ai_comment import comment_on
from bybit_api import get_current_price_and_trend

# Главное меню
def get_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Найти точку входа", callback_data="entry_point")],
        [InlineKeyboardButton("📰 Новости + Объем", callback_data="news_volume")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("🔍 Курс монеты", callback_data="check_price")],
        [InlineKeyboardButton("🚫 Заглушка", callback_data="stub_2")],
    ])

# Команда /start
async def start(update, context):
    keyboard = get_main_keyboard()
    if update.message:
        await update.message.reply_text("Выберите действие:", reply_markup=keyboard)
    elif update.callback_query:
        await update.callback_query.message.edit_text("Выберите действие:", reply_markup=keyboard)

# Обработка нажатий кнопок
async def button_handler(update, context):
    query = update.callback_query
    await query.answer()

    if query.data == "entry_point":
        await query.edit_message_text("🔄 Расчет точки входа...", reply_markup=get_main_keyboard())
        await find_signals(context.bot, chat_id=query.message.chat_id)
    elif query.data == "news_volume":
        await query.edit_message_text("🔄 Получение новостей и анализа...", reply_markup=get_main_keyboard())
        await find_news_with_volume_spike(context.bot, chat_id=query.message.chat_id)
    elif query.data == "check_price":
        await query.edit_message_text("Введите тикер монеты (например: ton):")
        context.user_data["awaiting_symbol"] = True
    elif query.data.startswith("stub"):
        await query.edit_message_text("🚫 Функция в разработке", reply_markup=get_main_keyboard())
    elif query.data.startswith("ai_comment"):
        _, symbol, rsi, volume = query.data.split("|")
        ai = comment_on(symbol, float(rsi), float(volume))
        msg = f"💮 AI-комментарий по {symbol}:\n{ai}"
        await context.bot.send_message(chat_id=query.message.chat_id, text=msg, reply_markup=get_main_keyboard())
    elif query.data == "start":
        await start(update, context)
    elif query.data == "stats":
        await query.edit_message_text("📊 Статистика за последние сутки:\n(в разработке)", reply_markup=get_main_keyboard())

# Обработка сообщений от пользователя
async def message_handler(update, context):
    if context.user_data.get("awaiting_symbol"):
        symbol = update.message.text.strip().upper()
        context.user_data["awaiting_symbol"] = False

        try:
            price, trend = get_current_price_and_trend(symbol)
            link = f"https://www.bybit.com/trade/usdt/{symbol}"
            msg = f"💱 {symbol} сейчас: ${price:.4f}\n📈 Тренд: {trend}\n🔗 [Фьючерсы на Bybit]({link})"
        except Exception as e:
            msg = f"❌ Ошибка при получении данных по {symbol}: {e}"

        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=get_main_keyboard())

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
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))

    print("✅ Бот запущен.")

    # Отправка стартового сообщения при запуске
    if CHAT_ID != "your_chat_id_here":
        try:
            await app.bot.send_message(chat_id=CHAT_ID, text="✅ Бот запущен. Выберите действие:", reply_markup=get_main_keyboard())
        except Exception as e:
            print(f"❌ Не удалось отправить стартовое меню: {e}")

    async def post_init():
        app.create_task(scheduled_scanner(app.bot))

    await app.initialize()
    await app.start()
    await post_init()
    await app.updater.start_polling()
    await app.updater.idle()

# Для запуска через run_forever.py
def run_bot():
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "event loop is already running" in str(e):
            print("⚠️ Event loop уже запущен. Пробуем альтернативный запуск...")
            loop = asyncio.get_event_loop()
            loop.create_task(main())
            loop.run_forever()
        else:
            raise
