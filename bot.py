import logging
import os
from dotenv import load_dotenv
from httpx import Timeout
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

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
print("RENDER / .ENV DIAGNOSTIC (FINAL LEGACY)")
print("=" * 50)
print(f"TELEGRAM_TOKEN: {'OK' if TELEGRAM_TOKEN else 'MISSING'}")
print(f"GIGACHAT_API_KEY: {'OK' if GIGACHAT_KEY else 'MISSING'}")
print("=" * 50)


# --- ФУНКЦИИ БОТА (СТАРЫЙ СТИЛЬ) ---
# Здесь мы добавляем 'bot=context.bot' в аргументы, так как нет use_context

def start(update: Update, context) -> None:
    user_first_name = update.effective_user.first_name
    if not TELEGRAM_TOKEN:
        update.message.reply_text(f"Привет, {user_first_name}! Я в режиме ДЕБАГ.")
        return
    
    # В старых версиях контекст не имеет bot по умолчанию
    bot = context.bot
    bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Привет, {user_first_name}! Я Бот-Друган на GigaChat. \n\nНапиши мне что-нибудь.",
        reply_markup=ForceReply(selective=True)
    )

def echo(update: Update, context) -> None:
    user_message = update.message.text
    user_first_name = update.effective_user.first_name

    if not GIGACHAT_KEY:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"{user_first_name}, ключ GigaChat не настроен.")
        return

    context.bot.send_message(chat_id=update.effective_chat.id, text="Думаю... 🤔")

    try:
        from gigachat import GigaChat
        
        client = GigaChat(
            scope="GIGACHAT_API_PERS", 
            credentials=GIGACHAT_KEY,
            verify_ssl_certs=False
        )
        
        response = client.chat(messages=user_message)
        context.bot.send_message(chat_id=update.effective_chat.id, text=response.text)

    except Exception as e:
        logger.error(f"Ошибка GigaChat: {e}")
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"{user_first_name}, ошибка при обращении к GigaChat.")

def main() -> None:
    if not TELEGRAM_TOKEN:
        logger.critical("CRITICAL: TELEGRAM_TOKEN is missing.")
        return 

    # --- САМЫЙ ПРОСТОЙ ВЫЗОВ ---
    # Только токен, никаких use_context, никаких очередей
    updater = Updater(TELEGRAM_TOKEN)
    
    dispatcher = updater.dispatcher

    # Используем старый Filters вместо filters
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    print("Бот запущен (Legacy mode). Ожидаю сообщения...")
    
    updater.start_polling(drop_pending_updates=True)
    updater.idle()

if __name__ == "__main__":
    main()
