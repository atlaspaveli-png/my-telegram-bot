import logging
import os
from dotenv import load_dotenv
from httpx import Timeout
from telegram import Update, ForceReply
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# --- ЗАГРУЗКА ПЕРЕМЕННЫХ ---
load_dotenv()

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GIGACHAT_KEY = os.environ.get("GIGACHAT_API_KEY")

# --- ЛОГИРОВАНИЕ ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- ДИАГНОСТИКА ---
print("=" * 50)
print("RENDER / .ENV DIAGNOSTIC")
print("=" * 50)
print(f"TELEGRAM_TOKEN: {'OK' if TELEGRAM_TOKEN else 'MISSING'}")
if TELEGRAM_TOKEN:
    print(f"Telegram Token: ...{TELEGRAM_TOKEN[-10:]}")
print(f"GIGACHAT_API_KEY: {'OK' if GIGACHAT_KEY else 'MISSING'}")
print("=" * 50)


# --- ФУНКЦИИ БОТА ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_first_name = update.effective_user.first_name
    if not TELEGRAM_TOKEN:
        await update.message.reply_text(f"Привет, {user_first_name}! Я в режиме ДЕБАГ.")
        return
    await update.message.reply_text(
        f"Привет, {user_first_name}! Я Бот-Друган на GigaChat. \n\nНапиши мне что-нибудь.",
        reply_markup=ForceReply(selective=True),
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    user_first_name = update.effective_user.first_name

    if not GIGACHAT_KEY:
        await update.message.reply_text(f"{user_first_name}, ключ GigaChat не настроен.")
        return

    await update.message.reply_text("Думаю... 🤔")

    try:
        from gigachat import GigaChat
        
        client = GigaChat(
            scope="GIGACHAT_API_PERS", 
            credentials=GIGACHAT_KEY,
            verify_ssl_certs=False
        )
        
        response = client.chat(messages=user_message)
        await update.message.reply_text(response.text)

    except Exception as e:
        logger.error(f"Ошибка GigaChat: {e}")
        await update.message.reply_text(f"{user_first_name}, ошибка при обращении к GigaChat.")

def main() -> None:
    if not TELEGRAM_TOKEN:
        logger.critical("CRITICAL: TELEGRAM_TOKEN is missing.")
        return 

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # --- ГЛАВНОЕ ИЗМЕНЕНИЕ ТУТ ---
    # Используем run_polling вместо run_webhook
    print("Бот запущен в режиме POLLING. Ожидаю сообщения...")
    
    # drop_pending_updates=True нужно, чтобы бот не спамил старыми сообщениями 
    # после перезапуска на сервере.
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
