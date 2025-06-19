import os
import requests
import pandas as pd
import numpy as np
import asyncio
from telegram import Bot
from telegram.error import TelegramError
from datetime import datetime


# Конфигурация
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
CRYPTOPANIC_API_KEY = os.getenv('CRYPTO_PANIC_KEY')

# Параметры анализа
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
VOLUME_SPIKE_MULTIPLIER = 2.5
MIN_PRICE_CHANGE = 3  # Минимальное изменение цены в % для сигнала

class BybitAnalyzer:
    def __init__(self):
        self.base_url = "https://api.bybit.com"

    def get_all_symbols(self):
        """Получаем все USDT-пары с Bybit"""
        url = f"{self.base_url}/v5/market/instruments-info"
        params = {'category': 'linear'}
        response = requests.get(url, params=params)
        data = response.json()
        return [
            item['symbol']
            for item in data['result']['list']
            if item['quoteCoin'] == 'USDT' and item['status'] == 'Trading'
        ]

    def get_klines(self, symbol, interval='5'):
        url = f"{self.base_url}/v5/market/kline"
        params = {
            'category': 'linear',
            'symbol': symbol,
            'interval': interval,
            'limit': 100
        }
        response = requests.get(url, params=params)
        data = response.json()
        return data['result']['list'] if 'result' in data else None

    def calculate_rsi(self, closes, period=14):
        deltas = np.diff(closes)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum()/period
        down = -seed[seed < 0].sum()/period
        rs = up/down
        rsi = np.zeros_like(closes)
        rsi[:period] = 100. - 100./(1.+rs)

        for i in range(period, len(closes)):
            delta = deltas[i-1]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta

            up = (up*(period-1) + upval)/period
            down = (down*(period-1) + downval)/period
            rs = up/down
            rsi[i] = 100. - 100./(1.+rs)

        return rsi[-1]

    def analyze_market(self, symbol):
        klines = self.get_klines(symbol)
        if not klines:
            return None

        df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
        df = df.iloc[::-1]  # Reverse to get chronological order

        # Convert to numeric
        df['close'] = pd.to_numeric(df['close'])
        df['volume'] = pd.to_numeric(df['volume'])

        # Calculate indicators
        current_price = df['close'].iloc[-1]
        rsi = self.calculate_rsi(df['close'].values)

        # Volume analysis
        avg_volume = df['volume'].rolling(20).mean().iloc[-1]
        current_volume = df['volume'].iloc[-1]
        volume_spike = current_volume > avg_volume * VOLUME_SPIKE_MULTIPLIER

        # Price change analysis (3 последние свечи)
        price_change = (df['close'].iloc[-1] - df['close'].iloc[-3]) / df['close'].iloc[-3] * 100

        return {
            'symbol': symbol,
            'price': current_price,
            'rsi': rsi,
            'volume': current_volume,
            'avg_volume': avg_volume,
            'volume_spike': volume_spike,
            'price_change': price_change
        }

class AIChat:
    def __init__(self):
        self.api_key = OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1/chat/completions"

    def generate_signal_comment(self, analysis):
        prompt = f"""
        На основе данных по {analysis['symbol']} дай краткий анализ на русском:
        - Текущая цена: {analysis['price']}
        - RSI: {analysis['rsi']:.2f}
        - Объем: {analysis['volume']:.2f} (Средний: {analysis['avg_volume']:.2f})
        - Изменение цены (3 свечи): {analysis['price_change']:.2f}%

        Анализ должен быть 1-2 предложения, профессиональный тон.
        Если RSI > {RSI_OVERBOUGHT}, укажи на перекупленность.
        Если RSI < {RSI_OVERSOLD}, укажи на перепроданность.
        """

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }

        response = requests.post(self.base_url, headers=headers, json=data)
        return response.json()['choices'][0]['message']['content']

class CryptoNews:
    def get_news_sentiment(self, coin):
        url = f"https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTOPANIC_API_KEY}&currencies={coin}"
        response = requests.get(url)
        data = response.json()
        return data['results'][0]['title'] if data['results'] else "Новостей нет"

class TradingSignalBot:
    def __init__(self):
        self.bot = Bot(token=TELEGRAM_BOT_TOKEN)
        self.analyzer = BybitAnalyzer()
        self.ai = AIChat()
        self.news = CryptoNews()
        self.symbols = self.analyzer.get_all_symbols()

    async def generate_signal(self, symbol):
        analysis = self.analyzer.analyze_market(symbol)
        if not analysis:
            return None

        # Определяем сигнал
        if (analysis['rsi'] > RSI_OVERBOUGHT and
            analysis['volume_spike'] and
            analysis['price_change'] > MIN_PRICE_CHANGE):

            signal = "ШОРТ"
            target_price = analysis['price'] * 0.98  # Цель -2%

        elif (analysis['rsi'] < RSI_OVERSOLD and
              analysis['volume_spike'] and
              analysis['price_change'] < -MIN_PRICE_CHANGE):

            signal = "ЛОНГ"
            target_price = analysis['price'] * 1.02  # Цель +2%
        else:
            return None

        # Генерация сообщения
        ai_comment = self.ai.generate_signal_comment(analysis)
        coin = symbol.replace('USDT', '')
        news = self.news.get_news_sentiment(coin)

        message = f"""
📱 Сигнал по {analysis['symbol']}
💰 Цена: {analysis['price']:.4f}
📊 RSI: {analysis['rsi']:.2f}
📦 Объём: {analysis['volume']:.2f} (Ср: {analysis['avg_volume']:.2f})
📉 Рекомендация: {signal}
🎯 Цель: {target_price:.4f}
📰 Новости: {news}
🤖 AI: "{ai_comment}"
🔗 Торговать: https://www.bybit.com/trade/usdt/{coin}
        """

        return message

    async def check_all_pairs(self):
        signals = []
        for symbol in self.symbols[:50]:  # Проверяем первые 50 пар (можно убрать ограничение)
            try:
                signal = await self.generate_signal(symbol)
                if signal:
                    signals.append(signal)
                    print(f"Найден сигнал для {symbol}")
            except Exception as e:
                print(f"Ошибка анализа {symbol}: {e}")

        return signals

    async def send_signals(self):
        try:
            signals = await self.check_all_pairs()
            if signals:
                for signal in signals:
                    await self.bot.send_message(
                        chat_id=TELEGRAM_CHAT_ID,
                        text=signal,
                        parse_mode='Markdown'
                    )
                print(f"Отправлено {len(signals)} сигналов")
            else:
                print("Сигналов не обнаружено")
        except Exception as e:
            print(f"Ошибка отправки: {e}")

async def main():
    bot = TradingSignalBot()
    while True:
        await bot.send_signals()
        await asyncio.sleep(300)  # Проверка каждые 5 минут

if __name__ == "__main__":
    asyncio.run(main())