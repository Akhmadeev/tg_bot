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
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = get_main_keyboard()
    if update.message:
        await update.message.reply_text("Выберите действие:", reply_markup=keyboard)
    elif update.callback_query:
        await update.callback_query.message.edit_text("Выберите действие:", reply_markup=keyboard)

# Обработка нажатий кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "entry_point":
        await query.edit_message_text("🔄 Расчет точки входа...", reply_markup=get_main_keyboard())
        await find_signals(context.bot, chat_id=query.message.chat.id)
    elif data == "news_volume":
        await query.edit_message_text("🔄 Получение новостей и анализа...", reply_markup=get_main_keyboard())
        await find_news_with_volume_spike(context.bot, chat_id=query.message.chat.id)
    elif data == "check_price":
        await query.edit_message_text("Введите тикер монеты (например: TON):")
               context.user_data["awaiting_symbol"] = True
    elif data.startswith("stub"):
        await query.edit_message_text("🚫 Функция в разработке", reply_markup=get_main_keyboard())
    elif data.startswith("ai_comment"):
        try:
            _, symbol, rsi, volume = data.split("|")
            ai = comment_on(symbol, float(rsi), float(volume))
            msg = f"🧐 AI-комментарий по {symbol}:\n{ai}"
            await context.bot.send_message(chat_id=query.message.chat.id, text=msg, reply_markup=get_main_keyboard())
        except Exception as e:
            await context.bot.send_message(chat_id=query.message.chat.id, text=f"Ошибка в AI-комментарии: {e}", reply_markup=get_main_keyboard())
    elif data == "start":
        await start(update, context)
    elif data == "stats":
        await query.edit_message_text("📊 Статистика за последние сутки:\n(в разработке)", reply_markup=get_main_keyboard())
    else:
        await query.edit_message_text("❌ Неизвестная команда", reply_markup=get_main_keyboard())

# Обработка сообщений от пользователя (например, ввод тикера)
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_symbol"):
        symbol = update.message.text.strip().upper()
        context.user_data["awaiting_symbol"] = False

        try:
            price, trend = get_current_price_and_trend(symbol)
            link = f"https://www.bybit.com/trade/usdt/{symbol}"
            msg = (f"💱 {symbol} сейчас: ${price:.4f}\n"
                   f"📈 Тренд: {trend}\n"
                   f"🔗 <a href='{link}'>Фьючерсы на Bybit</a>")
            await update.message.reply_text(msg, parse_mode="HTML", reply_markup=get_main_keyboard())
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка при получении данных по {symbol}: {e}", reply_markup=get_main_keyboard())
    else:
        await update.message.reply_text("Пожалуйста, выберите действие из меню.", reply_markup=get_main_keyboard())

# Периодический анализ (запускается в фоне)
async def scheduled_scanner(bot):
    while True:
        try:
            await find_signals(bot)
        except Exception as e:
            print(f"Ошибка в scheduled_scanner: {e}")
        await asyncio.sleep(300)

# Основной запуск бота
async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))

    print("✅ Бот запущен.")

    # Отправка стартового меню при запуске
    if CHAT_ID != "your_chat_id_here":
        try:
            # Удаляем вызов get_chat_history — его нет в библиотеке!
            await app.bot.send_message(chat_id=CHAT_ID, text="Бот запущен. Выберите действие:", reply_markup=get_main_keyboard())
        except Exception as e:
            print(f"❌ Не удалось отправить стартовое меню: {e}")

    async def post_init():
        app.create_task(scheduled_scanner(app.bot))

    await app.initialize()
    await app.start()
    await post_init()
    await app.updater.start_polling()
    await app.updater.idle()

# Функция для запуска из run_forever.py
def run_bot():
    asyncio.run(main())
