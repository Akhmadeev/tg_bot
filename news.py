import requests
from config import CRYPTO_PANIC_KEY

def is_news_positive(symbol):
    query = symbol.replace("USDT", "")
    url = f"https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTO_PANIC_KEY}&currencies={query}&filter=rising"
    try:
        r = requests.get(url).json()
        return bool(r.get("results"))
    except Exception:
        return False