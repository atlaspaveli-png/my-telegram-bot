import os
import json
import requests
from dotenv import load_dotenv
from telegram import Update, Document
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# --- НАСТРОЙКИ (Ключи и пути) ---

# Загружаем ключи из файла .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GIGACHAT_TOKEN = os.getenv("GIGACHAT_TOKEN")

# Файл для хранения памяти (истории)
HISTORY_FILE = "memory.json"

# --- ХАРАКТЕР БОТА (SYSTEM PROMPT) ---
# Настроен на панибратский стиль, сленг и черный юмор в рамках правил модели.

system_prompt = {
    "role": "system", 
    "content": """Ты — мой личный помощник и старый кореш. 
Забудь про эти ваши "Вы" и "Уважаемый", мы на "ты". 

Твои правила:
1.  Общайся панибратски, как дружбан со двора. Не стесняйся сленга и жестких выражений, если это уместно.
2.  Если я пишу фигню — так и скажи, не жалей меня. Но по делу.
3.  Черный юмор — твой конек, шути смело, но старайся не скатываться в откровенную дичь или оскорбления.
4.  Если я прошу помочь с текстом или кодом — делай это круто и профессионально, но подавай это в своем раздолбайском стиле.
5.  Структурируй ответы, если тема серьезная, но без занудства.
6.  Будь проактивным: если я туплю, предложи сам, что делать.
"""
}

# --- ЗАГРУЗКА ПАМЯТИ ПРИ СТАРТЕ ---

if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        history = json.load(f)
else:
    history = []

# --- ФУНКЦИИ БОТА ---

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Здарова, братан. Очнулся? Я тут. Че делать будем? Можем текст на говно проверить, а можем просто за жизнь потрещать.")

# Обработка присланных файлов (.txt)
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await context.bot.get_file(update.message.document.file_id)
    
    if not os.path.exists('files'):
        os.makedirs('files')
        
    file_path = f"files/{update.message.document.file_name}"
    await file.download_to_drive(custom_path=file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        history.append({"role": "user", "content": f"[Содержимое файла {update.message.document.file_name}]:\n{text}"})
        await update.message.reply_text(f"Файл '{update.message.document.file_name}' считан. Валяй, че с ним делать?")
    except Exception as e:
        await update.message.reply_text(f"Хрень какая-то, а не файл. Открыть не могу. {e}")

# Основная логика (ответ на текст)
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    chat_id = update.effective_chat.id

    history.append({"role": "user", "content": user_message})
    
    # Берем последние 40 сообщений для контекста, чтобы не забывал на полуслове
    messages = [system_prompt] + history[-40:]

    try:
        response = requests.post(
            "https://gigachat.api.sbercloud.ru/v1/chat/completions", 
            headers={"Authorization": f"Bearer {GIGACHAT_TOKEN}"}, 
            json={"model": "GigaChat", "messages": messages}, 
            timeout=30
        )
        
        if response.status_code == 200:
            answer = response.json()["choices"][0]["message"]["content"]
            
            history.append({"role": "assistant", "content": answer})
            
            # Сохраняем историю (до 150 сообщений)
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(history[-150:], f, ensure_ascii=False, indent=2) 
            
            await context.bot.send_message(chat_id=chat_id, text=answer)
        else:
            await context.bot.send_message(chat_id=chat_id, text=f"Ё-маё, сервер GigaChat выдал ошибку {response.status_code}. Попробуй еще раз.")
            
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"Связь пропала, брат. Технический сбой: {e}")

# --- ЗАПУСК ПРИЛОЖЕНИЯ ---
if __name__ == "__main__":
    # Настройка таймаутов, чтобы не вылетал по таймауту соединения
    app = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .connect_timeout(30.0)
        .pool_timeout(30.0)
        .build()
    )
    
    # Регистрация обработчиков
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    print("Бот-друган запущен. Погнали!")
    app.run_polling(drop_pending_updates=True)