import os
import logging
from httpx import Timeout
from telegram import Update, ForceReply
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# --- НАСТРОЙКИ ---
# Настройки для GigaChat
GIGACHAT_KEY = os.environ.get("GIGACHAT_API_KEY")

# --- ЛОГИРОВАНИЕ ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- ДИАГНОСТИКА (Вывод в лог) ---
print("=" * 50)
print("RENDER ENVIRONMENT DIAGNOSTIC")
print("=" * 50)

# Пытаемся получить токены
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
RENDER_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")

print(f"TELEGRAM_TOKEN найден: {'ДА' if TELEGRAM_TOKEN else 'НЕТ'}")
if TELEGRAM_TOKEN:
    # Показываем только начало и конец токена для безопасности в логах
    print(f"Значение: ...{TELEGRAM_TOKEN[-10:]}")
else:
    print("ВНИМАНИЕ: Переменная TELEGRAM_TOKEN пустая или отсутствует!")

print(f"RENDER_HOSTNAME найден: {'ДА' if RENDER_HOSTNAME else 'НЕТ'}")
print(f"GIGACHAT_API_KEY найден: {'ДА' if GIGACHAT_KEY else 'НЕТ'}")
print("=" * 50)
print("КОНЕЦ ДИАГНОСТИКИ")
print("=" * 50)


# --- ФУНКЦИИ БОТА ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not TELEGRAM_TOKEN:
        await update.message.reply_text("Я в режиме ДЕБАГ. Токен не настроен.")
    else:
        await update.message.reply_text(
            "Привет! Я Бот-Друган на GigaChat. Я живу на Render.com."
        )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text

    # Если нет ключа GigaChat
    if not GIGACHAT_KEY:
        await update.message.reply_text("Ошибка: Ключ GigaChat не настроен на сервере.")
        return

    await update.message.reply_text("Думаю...")

    try:
        from gigachat import GigaChat
        
        client = GigaChat(
            scope="GIGACHAT_API_PERS", 
            credentials=GIGACHAT_KEY,
            verify_ssl_certs=False # Важно для Render
        )
        
        response = client.chat(messages=user_message)
        await update.message.reply_text(response.text)

    except Exception as e:
        logger.error(f"Ошибка GigaChat: {e}")
        await update.message.reply_text("Ошибка при обращении к GigaChat. См. логи сервера.")

def main() -> None:
    # --- ЗАПУСК ---
    
    # Если токена нет, мы не создаем Application, чтобы не падать
    if not TELEGRAM_TOKEN:
        logger.critical("CRITICAL: TELEGRAM_TOKEN is missing. Bot will not start.")
        print("Бот остановлен из-за отсутствия TELEGRAM_TOKEN. Добавь переменную в Render.")
        return # Выходим из функции main, бот не запускается

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Настройки для Webhook на Render
    port = int(os.environ.get("PORT", "8080"))
    
    # Используем переменную RENDER_HOSTNAME, которую мы проверили выше
    if RENDER_HOSTNAME:
        webhook_url = f"https://{RENDER_HOSTNAME}:{port}/{TELEGRAM_TOKEN}"
    else:
        # Fallback если переменная RENDER_EXTERNAL_HOSTNAME не пришла
        logger.warning("RENDER_EXTERNAL_HOSTNAME not found. Webhook URL might be incorrect.")
        webhook_url = f"https://0.0.0.0:{port}/{TELEGRAM_TOKEN}"

    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=TELEGRAM_TOKEN,
        webhook_url=webhook_url
    )

if __name__ == "__main__":
    main()
