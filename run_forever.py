#!/usr/bin/env python3
import asyncio
import logging
from bot import TradingSignalBot  # Импорт вашего основного бота

# Настройка логгирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def run_bot():
    while True:
        try:
            bot = TradingSignalBot()
            await bot.send_signals()  # Или ваш основной метод
            await asyncio.sleep(300)  # Интервал проверки (5 минут)
        except Exception as e:
            logger.error(f"Ошибка: {e}", exc_info=True)
            await asyncio.sleep(60)  # Пауза перед перезапуском

if __name__ == "__main__":
    logger.info("🚀 Запуск бота в бесконечном цикле...")
    asyncio.run(run_bot())