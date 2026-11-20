import logging
import os
from dotenv import load_dotenv
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext

# --- ЗАГРУЗКА ПЕРЕМЕННЫХ ---
# Читаем файл .env, если он есть
load_dotenv()

# Получаем токены из системы (Environment Variables)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GIGACHAT_KEY = os.environ.get("GIGACHAT_API_KEY")

# --- НАСТРОЙКА ЛОГИРОВАНИЯ ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- ДИАГНОСТИКА (Вывод в консоль при старте) ---
print("=" * 60)
print("ЗАПУСК БОТА: ДИАГНОСТИКА")
print("=" * 60)
print(f"TELEGRAM_TOKEN: {'OK' if TELEGRAM_TOKEN else 'ОТСУТСТВУЕТ'}")
print(f"GIGACHAT_API_KEY: {'OK' if GIGACHAT_KEY else 'ОТСУТСТВУЕТ'}")
print("=" * 60)


# --- ОБРАБОТЧИКИ КОМАНД ---

def start(update: Update, context: CallbackContext) -> None:
    """Функция для команды /start"""
    user_first_name = update.effective_user.first_name
    
    if not TELEGRAM_TOKEN:
        update.message.reply_text(f"Привет, {user_first_name}! Я в режиме ОТЛАДКИ. Токен не настроен.")
        return

    update.message.reply_text(
        f"Привет, {user_first_name}! 👋\n"
        f"Я Бот-Друган на базе GigaChat.\n\n"
        "Напиши мне что-нибудь, и я отвечу.",
        reply_markup=ForceReply(selective=True),
    )

def echo(update: Update, context: CallbackContext) -> None:
    """Функция для ответа на любые текстовые сообщения"""
    user_message = update.message.text
    user_first_name = update.effective_user.first_name
    chat_id = update.effective_chat.id

    # Проверка ключа GigaChat
    if not GIGACHAT_KEY:
        context.bot.send_message(chat_id=chat_id, text=f"{user_first_name}, ошибка: Ключ GigaChat не настроен на сервере.")
        return

    context.bot.send_message(chat_id=chat_id, text="Думаю... 🤔")

    try:
        # Импортируем библиотеку только в момент использования
        from gigachat import GigaChat
        
        # Создаем клиента
        client = GigaChat(
            scope="GIGACHAT_API_PERS", 
            credentials=GIGACHAT_KEY,
            verify_ssl_certs=False # Важно для работы в облаках
        )
        
        # Получаем ответ от нейросети
        response = client.chat(messages=user_message)
        
        # Отправляем ответ пользователю
        context.bot.send_message(chat_id=chat_id, text=response.text)

    except Exception as e:
        # Если GigaChat упал, пишем в лог сервера и извиняемся перед пользователем
        logger.error(f"Критическая ошибка GigaChat: {e}")
        context.bot.send_message(chat_id=chat_id, text=f"{user_first_name}, произошла внутренняя ошибка. Попробуй позже.")


# --- ГЛАВНАЯ ФУНКЦИЯ ЗАПУСКА ---

def main() -> None:
    """Главная точка входа"""
    
    # Если токена нет в переменных окружения, бот не запустится
    if not TELEGRAM_TOKEN:
        logger.critical("FATAL: Переменная TELEGRAM_TOKEN не найдена. Бот остановлен.")
        return

    # === СТАРЫЙ СПОСОБ ЗАПУСКА (который не падает) ===
    # Создаем объект Updater напрямую, передавая только токен.
    # Это обходит баг с Application.builder() в новых версиях Python.
    updater = Updater(TELEGRAM_TOKEN)
    
    # Получаем диспетчера, чтобы регистрировать команды
    dispatcher = updater.dispatcher

    # Регистрируем обработчики
    dispatcher.add_handler(CommandHandler("start", start))
    # Обрабатываем любые текстовые сообщения, кроме команд
    dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    print("✅ Бот успешно инициализирован. Режим: POLLING (Опрос)")
    print("📡 Ожидаю сообщения от пользователей...")

    # Запускаем бесконечный цикл получения обновлений
    # drop_pending_updates=True нужен, чтобы при перезапуске бот не спамил старыми сообщениями
    updater.start_polling(drop_pending_updates=True)
    
    # Блокирует программу, чтобы она не закрылась
    updater.idle()


# --- СТАРТ ПРОГРАММЫ ---
if __name__ == "__main__":
    main()
