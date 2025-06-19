from bot import run_bot, auto_check
import threading
import time

def run_looped_analysis():
    while True:
        print("🔄 Автоматический анализ рынка...")
        auto_check()
        time.sleep(300)  # 5 минут

if __name__ == "__main__":
    # Запускаем автоанализ в отдельном потоке
    thread = threading.Thread(target=run_looped_analysis)
    thread.start()

    # Запускаем Telegram-бота
    run_bot()
