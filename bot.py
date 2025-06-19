from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import TELEGRAM_TOKEN, CHAT_ID
from bybit_api import get_all_spot_symbols, get_klines
from indicators import calculate_rsi
from ai_comment import comment_on
from news import is_news_positive
from chart import save_chart
import time
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TELEGRAM_TOKEN)


# 👇 async: Отправка одного сигнала по запросу
async def send_signals(context: ContextTypes.DEFAULT_TYPE = None):
    symbols = get_all_spot_symbols()
    found = False

    for symbol in symbols[:20]:  # ограничим до 20
        try:
            closes, volumes = get_klines(symbol)
            if len(closes) < 20:
                continue

            rsi = calculate_rsi(closes)[-1]
            volume_now = volumes[-1]
            volume_avg = sum(volumes[-10:]) / 10

            rsi_signal = rsi > 70 or rsi < 30
            volume_signal = volume_now > volume_avg * 2

            if (rsi_signal or volume_signal) and is_news_positive(symbol):
                msg = f"📱 Сигнал по {symbol}\nRSI: {rsi:.2f}\nОбъём: {volume_now:.2f}"
                ai = comment_on(symbol, rsi, volume_now)
                if ai:
                    msg += f"\n🤖 AI: {ai}"

                chart_path = save_chart(symbol, closes)
                await bot.send_photo(chat_id=CHAT_ID, photo=open(chart_path, "rb"), caption=msg)
                found = True
                break
        except Exception as e:
            print(f"[ERROR async] {symbol}: {e}")

    if not found:
        await bot.send_message(chat_id=CHAT_ID, text="🚫 Сигналы не найдены")


# 👇 sync: Автоматическая проверка (используется в run_forever)
def auto_check():
    symbols = get_all_spot_symbols()
    for symbol in symbols:
        try:
            closes, volumes = get_klines(symbol)
            if len(closes) < 20:
                continue

            rsi = calculate_rsi(closes)[-1]
            volume_now = volumes[-1]
            volume_avg = sum(volumes[-10:]) / 10

            rsi_signal = rsi > 70 or rsi < 30
            volume_signal = volume_now > volume_avg * 2

            if (rsi_signal or volume_signal) and is_news_positive(symbol):
                msg = f"📱 Сигнал по {symbol}\nRSI: {rsi:.2f}\nОбъём: {volume_now:.2f}"
                ai = comment_on(symbol, rsi, volume_now)
                if ai:
                    msg += f"\n🤖 AI: {ai}"

                chart_path = save_chart(symbol, closes)
                bot.send_photo(chat_id=CHAT_ID, photo=open(chart_path, "rb"), caption=msg)
                time.sleep(1)
        except Exception as e:
            print(f"[ERROR sync] {symbol}: {e}")


# 👇 /start меню
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔍 Найти точку входа", callback_data='find_signal')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)


# 👇 Обработка кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'find_signal':
        await query.edit_message_text("⏳ Поиск лучших точек входа...")
        await send_signals(context)


# 👇 Запуск Telegram-бота (параллельно с автоанализом)
def run_bot():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()
