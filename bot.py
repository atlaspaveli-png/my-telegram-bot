import os
import logging
from httpx import Timeout
from telegram import Update, ForceReply, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# --- НАСТРОЙКИ ---
# Токен бота берем из переменных окружения (безопасность)
TOKEN = os.environ.get("TELEGRAM_TOKEN")

# Ключ для GigaChat берем из переменных окружения
GIGACHAT_KEY = os.environ.get("GIGACHAT_API_KEY")

# Включаем логирование для отладки
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- ФУНКЦИИ БОТА ---

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Привет! Я Бот-Друган на GigaChat. Я запущен на сервере без VPN. "
        "Напиши мне что-нибудь, и я отвечу."
    )

# Обработка всех текстовых сообщений через GigaChat
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    
    # Проверяем, есть ли ключ
    if not GIGACHAT_KEY:
        await update.message.reply_text("Ошибка: Ключ GigaChat не настроен на сервере.")
        return

    await update.message.reply_text("Думаю...")

    try:
        # Импортируем GigaChat здесь, чтобы не ломать запуск, если библиотеки нет
        from gigachat import GigaChat
        
        # Инициализируем модель
        client = GigaChat(
            scope="GIGACHAT_API_PERS", 
            credentials=GIGACHAT_KEY,
            verify_ssl_certs=False # Важно для работы в некоторых облаках
        )
        
        # Отправляем запрос
        response = client.chat(messages=user_message)
        
        # Отправляем ответ пользователю
        await update.message.reply_text(response.text)

    except Exception as e:
        logger.error(f"Ошибка GigaChat: {e}")
        await update.message.reply_text("Произошла ошибка при обращении к GigaChat. Попробуй позже.")

def main() -> None:
    # Проверяем токен
    if not TOKEN:
        raise ValueError("Нет TELEGRAM_TOKEN в переменных окружения")

    # Создаем приложение
    application = Application.builder().token(TOKEN).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # --- ЗАПУСК ДЛЯ RENDER.COM ---
    # Используем Webhook, так как это веб-сервис
    port = int(os.environ.get("PORT", "8080")) # Порт, который дает Render
    
    # Используем run_webhook
    application.run_webhook(
        listen="0.0.0.0", 
        port=port,
        url_path=TOKEN,
        webhook_url=f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}:{port}/{TOKEN}"
    )

if __name__ == "__main__":
    main()
