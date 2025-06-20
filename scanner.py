from bybit_api import get_all_spot_symbols, get_klines
from indicators import calculate_rsi
from news import is_news_positive, get_hot_news_for_symbol
from chart import save_chart
from config import CHAT_ID
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def find_signals(bot, chat_id=None):
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

            if (rsi_signal or volume_signal):  # отключена проверка новостей временно
                direction = "LONG" if rsi < 30 else "SHORT"
                target_price = closes[-1] * (1.03 if direction == "LONG" else 0.97)

                msg = f"📈 Сигнал по {symbol}\nRSI: {rsi:.2f}\nОбъ𐄀м: {volume_now:.2f}\n\n🗓 Рекомендуется {direction} до {target_price:.4f}"
                msg += f"\n\n→ [Открыть на Bybit](https://www.bybit.com/trade/usdt/{symbol.replace('USDT', '')})"

                chart_path = save_chart(symbol, closes)
                with open(chart_path, "rb") as photo:
                    reply_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton("🧠 Запросить мнение AI", callback_data=f"ai_comment|{symbol}|{rsi:.2f}|{volume_now:.2f}")],
                        [InlineKeyboardButton("⬅️ Назад в меню", callback_data="start")]
                    ])
                    await bot.send_photo(chat_id=chat_id or CHAT_ID, photo=photo, caption=msg, parse_mode='Markdown', reply_markup=reply_markup)
        except Exception as e:
            print(f"[ERROR] {symbol}: {e}")

async def find_news_with_volume_spike(bot, chat_id=None):
    symbols = get_all_spot_symbols()
    for symbol in symbols:
        try:
            closes, volumes = get_klines(symbol)
            if len(closes) < 10:
                continue

            volume_now = volumes[-1]
            volume_avg = sum(volumes[-10:]) / 10
            volume_growth = (volume_now - volume_avg) / volume_avg * 100

            if 2 < volume_growth < 30:
                news = get_hot_news_for_symbol(symbol)
                if news:
                    msg = f"📰 Новости по {symbol} ( +{volume_growth:.2f}% объем):\n{news}"
                    reply_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton("⬅️ Назад в меню", callback_data="start")]
                    ])
                    await bot.send_message(chat_id=chat_id or CHAT_ID, text=msg, reply_markup=reply_markup)
        except Exception as e:
            print(f"[NEWS ERROR] {symbol}: {e}")
