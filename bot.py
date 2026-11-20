import logging
import os
from dotenv import load_dotenv
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
print("=" * 60)
print("ЗАПУСК БОТА: ДИАГНОСТИКА")
print("=" * 60)
print(f"TELEGRAM_TOKEN: {'OK' if TELEGRAM_TOKEN else 'ОТСУТСТВУЕТ'}")
print(f"GIGACHAT_API_KEY: {'OK' if GIGACHAT_KEY else 'ОТСУТСТВУЕТ'}")
print("=" * 60)


# --- ОБРАБОТЧИКИ ---

def start(update: Update, context: CallbackContext) -> None:
    """Команда /start"""
    user_first_name = update.effective_user.first_name
    
    if not TELEGRAM_TOKEN:
        update.message.reply_text(f"Привет, {user_first_name}! Я в режиме ОТЛАДКИ.")
        return

    update.message.reply_text(
        f"Привет, {user_first_name}! 👋\n"
        f"Я Бот-Друган на базе GigaChat.\n\n"
        "Напиши мне что-нибудь, и я отвечу.",
        reply_markup=ForceReply(selective=True),
    )

def echo(update: Update, context: CallbackContext) -> None:
    """Ответ на сообщения"""
    user_message = update.message.text
    user_first_name = update.effective_user.first_name
    chat_id = update.effective_chat.id

    if not GIGACHAT_KEY:
        context.bot.send_message(chat_id=chat_id, text=f"{user_first_name}, ключ GigaChat не настроен.")
        return

    context.bot.send_message(chat_id=chat_id, text="Думаю... 🤔")

    try:
        from gigachat import GigaChat
        
        client = GigaChat(
            scope="GIGACHAT_API_PERS", 
            credentials=GIGACHAT_KEY,
            verify_ssl_certs=False
        )
        
        # === ГЛАВНОЕ ИСПРАВЛЕНИЕ: меняем 'messages' на 'message' ===
        response = client.chat(message=user_message)
        
        context.bot.send_message(chat_id=chat_id, text=response.text)

    except Exception as e:
        logger.error(f"Ошибка GigaChat: {e}")
        context.bot.send_message(chat_id=chat_id, text=f"{user_first_name}, ошибка сервиса. Попробуй позже.")


# --- ГЛАВНАЯ ФУНКЦИЯ ---

def main() -> None:
    if not TELEGRAM_TOKEN:
        logger.critical("FATAL: TELEGRAM_TOKEN is missing.")
        return

    # Используем Updater (Legacy mode), чтобы избежать багов Python 3.13+
    updater = Updater(TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher

    # Регистрация команд
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    print("✅ Бот запущен в режиме POLLING. Ожидаю сообщения...")
    
    # Запуск бесконечного цикла
    updater.start_polling(drop_pending_updates=True)
    updater.idle()

if __name__ == "__main__":
    main()
