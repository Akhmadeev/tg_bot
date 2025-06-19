from telegram import Bot
from config import TELEGRAM_TOKEN, CHAT_ID
from bybit_api import get_all_spot_symbols, get_klines
from indicators import calculate_rsi
from ai_comment import comment_on
from news import is_news_positive
from chart import save_chart
import time

bot = Bot(token=TELEGRAM_TOKEN)

def find_signals():
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
                msg = f"\ud83d\udcf1 Сигнал по {symbol}\nRSI: {rsi:.2f}\nОбъём: {volume_now:.2f}"
                ai = comment_on(symbol, rsi, volume_now)
                if ai:
                    msg += f"\n\ud83e\udd16 AI: {ai}"

                chart_path = save_chart(symbol, closes)
                bot.send_photo(chat_id=CHAT_ID, photo=open(chart_path, "rb"), caption=msg)
                time.sleep(1)
        except Exception as e:
            print(f"[ERROR] {symbol}: {e}")