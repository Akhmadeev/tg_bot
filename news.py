import requests
from config import CRYPTO_PANIC_KEY

def is_news_positive(symbol: str) -> bool:
    news = get_hot_news_for_symbol(symbol)
    return any(word in news.lower() for word in ["grow", "gain", "rise", "bull", "surge"])

def get_hot_news_for_symbol(symbol: str) -> str:
    url = f"https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTO_PANIC_KEY}&currencies={symbol.replace('USDT', '')}&public=true"
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"[NEWS API ERROR] {symbol}: HTTP {response.status_code} - {response.text}")
            return "Ошибка при получении новостей."

        data = response.json()
        articles = data.get("results", [])
        if not articles:
            return "Нет свежих новостей."
        return articles[0]["title"] + "\n" + articles[0].get("url", "")
    except Exception as e:
        print(f"[NEWS API ERROR] {symbol}: {e}")
        return "Ошибка при получении новостей."
