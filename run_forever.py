import time
from bot import find_signals

while True:
    print("🔄 Запуск анализа рынка...")
    find_signals()
    print(" Готово. Ждём 5 минут...")
    time.sleep(300)
