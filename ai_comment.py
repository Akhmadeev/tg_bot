import openai
from config import OPENAI_API_KEY

def comment_on(symbol, rsi, volume):
    if not OPENAI_API_KEY:
        return None
    openai.api_key = OPENAI_API_KEY
    prompt = f"Что ты думаешь про монету {symbol}? RSI={rsi:.2f}, объём={volume:.2f}. Возможен ли рост или падение?"
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return None