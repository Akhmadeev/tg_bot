# bot.py
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import TELEGRAM_TOKEN, CHAT_ID
from bybit_api import get_all_spot_symbols, get_klines
from indicators import calculate_rsi
from ai_comment import comment_on
from news import is_news_positive
from chart import save_chart
import time
from datetime import datetime

bot = Bot(token=TELEGRAM_TOKEN)

# 🔍 Поиск сигналов
async def find_signals():
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
                direction = "🔼 ЛОНГ" if rsi < 30 else "🔽 ШОРТ"
                target_price = closes[-1] * (1.03 if rsi < 30 else 0.97)
                link = f"https://www.bybit.com/trade/usdt/{symbol.replace('USDT', '')}USDT"

                msg = (
                    f"📈 Сигнал по <b>{symbol}</b>\n"
                    f"RSI: {rsi:.2f}\n"
                    f"Объём: {volume_now:.2f}\n"
                    f"{direction}\n"
                    f"🎯 Цель: {target_price:.4f}\n"
                    f"🔗 <a href=\"{link}\">Торговать на фьючерсах</a>"
                )

                ai = comment_on(symbol, rsi, volume_now)
                if ai:
                    msg += f"\n🤖 AI: {ai}"

                chart_path = save_chart(symbol, closes)
                await bot.send_photo(chat_id=CHAT_ID, photo=open(chart_path, "rb"), caption=msg, parse_mode="HTML")
                await asyncio.sleep(1)

        except Exception as e:
            print(f"[ERROR] {symbol}: {e}")

# 📲 Команды Telegram-бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        keyboard = [
            [InlineKeyboardButton("🚀 Найти сигнал сейчас", callback_data="find_signal")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "find_signal":
        await query.edit_message_text("Ищу сигналы...")
        await find_signals()

# 🕒 Фоновая задача
async def scheduled_scanner():
    while True:
        print(f"🕒 Автопоиск {datetime.now().strftime('%H:%M:%S')}")
        await find_signals()
        await asyncio.sleep(600)  # каждые 10 минут

# 🚀 Запуск
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_button))

    # добавляем фоновую задачу
    app.create_task(scheduled_scanner())

    print("🔄 Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
