import logging
import os
from dotenv import load_dotenv
from httpx import Timeout
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext

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
print("RENDER / .ENV DIAGNOSTIC (FINAL)")
print("=" * 50)
print(f"TELEGRAM_TOKEN: {'OK' if TELEGRAM_TOKEN else 'MISSING'}")
print(f"GIGACHAT_API_KEY: {'OK' if GIGACHAT_KEY else 'MISSING'}")
print("=" * 50)


# --- ФУНКЦИИ БОТА ---

def start(update: Update, context: CallbackContext) -> None:
    user_first_name = update.effective_user.first_name
    if not TELEGRAM_TOKEN:
        update.message.reply_text(f"Привет, {user_first_name}! Я в режиме ДЕБАГ.")
        return
    update.message.reply_text(
        f"Привет, {user_first_name}! Я Бот-Друган на GigaChat. \n\nНапиши мне что-нибудь.",
        reply_markup=ForceReply(selective=True),
    )

def echo(update: Update, context: CallbackContext) -> None:
    user_message = update.message.text
    user_first_name = update.effective_user.first_name

    if not GIGACHAT_KEY:
        update.message.reply_text(f"{user_first_name}, ключ GigaChat не настроен.")
        return

    update.message.reply_text("Думаю... 🤔")

    try:
        from gigachat import GigaChat
        
        client = GigaChat(
            scope="GIGACHAT_API_PERS", 
            credentials=GIGACHAT_KEY,
            verify_ssl_certs=False
        )
        
        response = client.chat(messages=user_message)
        update.message.reply_text(response.text)

    except Exception as e:
        logger.error(f"Ошибка GigaChat: {e}")
        update.message.reply_text(f"{user_first_name}, ошибка при обращении к GigaChat.")

def main() -> None:
    if not TELEGRAM_TOKEN:
        logger.critical("CRITICAL: TELEGRAM_TOKEN is missing.")
        return 

    # --- ИСПРАВЛЕННАЯ СТРОКА ---
    # Используем Updater.new_key_in() или передаем None для очереди
    # Самый простой способ для v20:
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    
    dispatcher = updater.dispatcher

    # Регистрируем обработчики
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    print("Бот запущен (Fallback mode). Ожидаю сообщения...")
    
    # Запускаем бесконечный цикл опроса
    updater.start_polling(drop_pending_updates=True)
    updater.idle() # Держит бота запущенным

if __name__ == "__main__":
    main()
