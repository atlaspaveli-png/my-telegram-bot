import logging
import os
from dotenv import load_dotenv
from httpx import Timeout
from telegram import Update, ForceReply
from telegram.ext import Application, CommandHandler, MessageHandler, filters

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
print("RENDER / .ENV DIAGNOSTIC (V20)")
print("=" * 50)
print(f"TELEGRAM_TOKEN: {'OK' if TELEGRAM_TOKEN else 'MISSING'}")
print(f"GIGACHAT_API_KEY: {'OK' if GIGACHAT_KEY else 'MISSING'}")
print("=" * 50)


# --- ФУНКЦИИ БОТА ---

async def start(update: Update, context) -> None:
    user_first_name = update.effective_user.first_name
    if not TELEGRAM_TOKEN:
        await update.message.reply_text(f"Привет, {user_first_name}! Я в режиме ДЕБАГ.")
        return
    await update.message.reply_text(
        f"Привет, {user_first_name}! Я Бот-Друган на GigaChat. \n\nНапиши мне что-нибудь.",
        reply_markup=ForceReply(selective=True),
    )

async def echo(update: Update, context) -> None:
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

    # --- СОВРЕМЕННЫЙ СТИЛЬ (Application) ---
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    # Обратите внимание: filters.text & ~filters.command (с маленькой буквы!)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    print("Бот запущен (Modern v20). Ожидаю сообщения...")
    
    # Запуск в режиме опроса
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
