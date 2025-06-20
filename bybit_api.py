import requests

def get_current_price_and_trend(symbol: str):
    url = f"https://api.bybit.com/v2/public/tickers?symbol={symbol}USDT"
    response = requests.get(url)
    data = response.json()
    if data["ret_code"] != 0 or not data["result"]:
        raise Exception("Ошибка получения данных с Bybit")
    ticker = data["result"][0]
    price = float(ticker["last_price"])
    # Пример простого тренда:
    trend = "Вверх" if float(ticker["prev_price_24h"]) < price else "Вниз"
    return price, trend
