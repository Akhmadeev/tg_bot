import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from config import TELEGRAM_TOKEN
from bybit_api import get_current_price_and_trend

def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔥 Найти точку входа", callback_data="entry_point")],
        [InlineKeyboardButton("📊 Курс монеты", callback_data="check_price")],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Выберите действие:",
        reply_markup=get_main_keyboard()
    )
    context.user_data["awaiting_symbol"] = False

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "entry_point":
        await query.edit_message_text("Точка входа в разработке.", reply_markup=get_main_keyboard())
    elif query.data == "check_price":
        await query.edit_message_text("Введите тикер монеты (например: TON):")
        context.user_data["awaiting_symbol"] = True
    else:
        await query.edit_message_text("Неизвестная команда.", reply_markup=get_main_keyboard())

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_symbol"):
        symbol = update.message.text.strip().upper()
        context.user_data["awaiting_symbol"] = False
        try:
            price, trend = get_current_price_and_trend(symbol)
            link = f"https://www.bybit.com/trade/usdt/{symbol}"
            msg = (
                f"💱 {symbol} сейчас: ${price:.4f}\n"
                f"📈 Тренд: {trend}\n"
                f"🔗 <a href='{link}'>Фьючерсы на Bybit</a>"
            )
            await update.message.reply_text(msg, parse_mode="HTML", reply_markup=get_main_keyboard())
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {e}", reply_markup=get_main_keyboard())
    else:
        await update.message.reply_text("Пожалуйста, выберите действие из меню.", reply_markup=get_main_keyboard())

async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))

    print("✅ Бот запущен.")

    await app.run_polling()

def run_bot():
    asyncio.run(main())
