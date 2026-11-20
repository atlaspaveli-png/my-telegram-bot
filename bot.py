import logging
import os
from dotenv import load_dotenv
from httpx import Timeout
from telegram import Update, ForceReply
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# --- ЗАГРУЗКА ПЕРЕМЕННЫХ ИЗ ФАЙЛА .ENV ---
# Эта строчка говорит программе: "Проверь, есть ли файл .env рядом со мной, 
# и если есть — прочитай из него ключи".
load_dotenv()

# --- НАСТРОЙКИ (считываем из системы) ---
# Теперь бот ищет токены и в переменных Render, и в файле .env
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GIGACHAT_KEY = os.environ.get("GIGACHAT_API_KEY")

# --- ЛОГИРОВАНИЕ ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- ДИАГНОСТИКА (Вывод в лог при старте) ---
print("=" * 50)
print("RENDER / .ENV DIAGNOSTIC")
print("=" * 50)

# Проверяем, откуда бот взял данные
print(f"TELEGRAM_TOKEN: {'OK' if TELEGRAM_TOKEN else 'MISSING'}")
if TELEGRAM_TOKEN:
    print(f"Telegram Token: ...{TELEGRAM_TOKEN[-10:]}") # Показываем хвост токена

print(f"GIGACHAT_API_KEY: {'OK' if GIGACHAT_KEY else 'MISSING'}")
print(f"RENDER_HOSTNAME: {os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'N/A')}")
print("=" * 50)


# --- ФУНКЦИИ БОТА ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_first_name = update.effective_user.first_name
    
    if not TELEGRAM_TOKEN:
        await update.message.reply_text(f"Привет, {user_first_name}! Я в режиме ДЕБАГ. Токен не настроен.")
        return

    await update.message.reply_text(
        f"Привет, {user_first_name}! Я Бот-Друган на GigaChat. Я живу на Render.com. \n\n"
        "Напиши мне что-нибудь, и я отвечу.",
        reply_markup=ForceReply(selective=True),
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    user_first_name = update.effective_user.first_name

    # Проверка ключа GigaChat
    if not GIGACHAT_KEY:
        await update.message.reply_text(f"{user_first_name}, я не могу ответить: ключ GigaChat не настроен на сервере.")
        return

    await update.message.reply_text("Думаю... 🤔")

    try:
        from gigachat import GigaChat
        
        # Инициализируем модель
        client = GigaChat(
            scope="GIGACHAT_API_PERS", 
            credentials=GIGACHAT_KEY,
            verify_ssl_certs=False # Важно для работы в облаках
        )
        
        # Отправляем запрос
        response = client.chat(messages=user_message)
        
        # Отправляем ответ пользователю
        await update.message.reply_text(response.text)

    except Exception as e:
        logger.error(f"Ошибка GigaChat: {e}")
        await update.message.reply_text(f"{user_first_name}, произошла ошибка при обращении к GigaChat. Администратору сообщили.")

def main() -> None:
    # --- ПРОВЕРКА ЗАПУСКА ---
    if not TELEGRAM_TOKEN:
        logger.critical("CRITICAL: TELEGRAM_TOKEN is missing. Bot will not start.")
        print("Бот остановлен. Добавь TELEGRAM_TOKEN в .env или Environment Variables в Render.")
        return 

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Регистрируем команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # --- ЗАПУСК НА RENDER (Webhook) ---
    port = int(os.environ.get("PORT", "8080"))
    
    # Используем переменные, которые мы проверили выше
    hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
    
    if hostname:
        webhook_url = f"https://{hostname}:{port}/{TELEGRAM_TOKEN}"
    else:
        logger.warning("RENDER_EXTERNAL_HOSTNAME not found.")
        webhook_url = f"https://0.0.0.0:{port}/{TELEGRAM_TOKEN}"

    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=TELEGRAM_TOKEN,
        webhook_url=webhook_url
    )

if __name__ == "__main__":
    main()
