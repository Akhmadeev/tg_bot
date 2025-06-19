import time
from bot import find_signals

while True:
    print("\ud83d\udd04 Запуск анализа рынка...")
    find_signals()
    print("\u2705 Готово. Ждём 5 минут...")
    time.sleep(300)
