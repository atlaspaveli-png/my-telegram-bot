import logging
import os
import inspect  # <<< ЭТОЙ СТРОКИ НЕ ХВАТАЛО РАНЬШЕ
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

# --- ДИАГНОСТИКА ЗАПУСКА ---
print("=" * 60)
print("ЗАПУСК БОТА: ДИАГНОСТИКА")
print("=" * 60)
print(f"TELEGRAM_TOKEN: {'OK' if TELEGRAM_TOKEN else 'ОТСУТСТВУЕТ'}")
print(f"GIGACHAT_API_KEY: {'OK' if GIGACHAT_KEY else 'ОТСУТСТВУЕТ'}")
print("=" * 60)


# --- ОБРАБОТЧИК /start ---
def start(update: Update, context: CallbackContext) -> None:
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

# --- ОБРАБОТЧИК СООБЩЕНИЙ (ШПИОН) ---
def echo(update: Update, context: CallbackContext) -> None:
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

        # === ШПИОНСКАЯ ПРОВЕРКА (ТЕПЕРЬ ОНА РАБОТАЕТ) ===
        response = None
        
        try:
            sig = inspect.signature(client.chat)
            args_list = list(sig.parameters.keys())
            print(f"DEBUG: GigaChat.chat принимает аргументы: {args_list}")
        except Exception as e:
            print(f"DEBUG: Не удалось проверить сигнатуру: {e}")

        # 1. Пробуем 'message'
        try:
            response = client.chat(message=user_message)
        except TypeError:
            pass

        # 2. Пробуем 'messages'
        if response is None:
            try:
                response = client.chat(messages=user_message)
            except TypeError:
                pass

        # 3. Пробуем просто текст
        if response is None:
            try:
                response = client.chat(user_message)
            except TypeError:
                pass

        # 4. Пробуем 'text'
        if response is None:
            try:
                response = client.chat(text=user_message)
            except TypeError:
                pass

        # Если ничего не подошло
        if response is None:
            logger.error("Все варианты вызова GigaChat провалились.")
            context.bot.send_message(chat_id=chat_id, text="Ошибка: не подошел ни один аргумент.")
            return

        # Успех
        context.bot.send_message(chat_id=chat_id, text=response.text)

    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        context.bot.send_message(chat_id=chat_id, text=f"{user_first_name}, критическая ошибка.")


# --- ГЛАВНАЯ ТОЧКА ---
def main() -> None:
    if not TELEGRAM_TOKEN:
        logger.critical("FATAL: TELEGRAM_TOKEN is missing.")
        return

    updater = Updater(TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    print("✅ Бот запущен в режиме POLLING. Ожидаю сообщения...")
    
    updater.start_polling(drop_pending_updates=True)
    updater.idle()

if __name__ == "__main__":
    main()
