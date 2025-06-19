import requests

def get_all_spot_symbols():
    url = "https://api.bybit.com/v5/market/tickers?category=spot"
    data = requests.get(url).json()
    return [x['symbol'] for x in data['result']['list'] if x['symbol'].endswith("USDT")]

def get_klines(symbol, interval="15"):
    url = f"https://api.bybit.com/v5/market/kline?category=spot&symbol={symbol}&interval={interval}&limit=100"
    r = requests.get(url).json()
    candles = r.get("result", {}).get("list", [])
    closes = [float(c[4]) for c in candles]
    volumes = [float(c[5]) for c in candles]
    return closes, volumes
