print("✅ Бот запущен. Ожидаю сообщения...")

import uuid
import os
import json
import httpx
import asyncio
import random
import edge_tts

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, CommandHandler, filters

# 🔑 Токены
TELEGRAM_TOKEN = "7267160308:AAHy7UC8LvsmfFhrM4n559d3jKc89UjhEwU"
OPENROUTER_API_KEY = "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"

# 💾 История сообщений и заметки
user_histories = {}
user_notes = {}
user_voice_mode = {}

# 📋 Файл пользователей
USER_FILE = "users.json"

def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            return json.load(f)
    return []

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f)

# ⌨️ Клавиатура
keyboard = [
    [KeyboardButton("🧠 Задать вопрос"), KeyboardButton("📚 Интересный факт")],
    [KeyboardButton("📝 Мои заметки"), KeyboardButton("⏰ Напоминание")],
    [KeyboardButton("🔊 Ответ голосом")],
    [KeyboardButton("ℹ️ Помощь"), KeyboardButton("📩 Связь с владельцем")]
]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        save_users(users)
        await update.message.reply_text("👋 Привет! Я вижу, ты тут впервые. Рад знакомству!")

    await update.message.reply_text(
        "🤖 Я бот на базе ChatGPT. Выбери действие ниже или задай вопрос!",
        reply_markup=reply_markup
    )

# /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""\
🤖 Pavel Assistant — твой помощник!

🧠 Задать вопрос — отправь запрос к GPT  
📚 Интересный факт — узнай что-то новое  
📝 Мои заметки — покажу все твои заметки  
⏰ Напоминание — команда /remind <секунды> <текст>  
🔊 Ответ голосом — следующий ответ я озвучу
""", parse_mode="Markdown")

# Интересные факты
facts = [
    "Улитки могут спать до 3 лет подряд.",
    "На Сатурне и Юпитере идёт дождь из алмазов.",
    "Коты могут издавать более 100 различных звуков.",
    "В Африке есть озеро, которое может убивать животных — озеро Натрон.",
    "Пингвины предлагают камушки своим партнёрам, как символ любви.",
    "Человеческое сердце может создавать давление, способное брызнуть кровью на 9 метров.",
    "Осьминоги имеют три сердца и синюю кровь.",
    "Некоторые черепахи могут дышать через задний проход.",
    "Каждые 7 лет клетки в нашем теле полностью обновляются (почти все).",
    "Грозы на Юпитере в 1000 раз мощнее земных.",
    "Молоко бегемота розового цвета.",
    "На Марсе закаты синие.",
    "Сова не может повернуть глаза — только голову на 270°.",
    "Муравьи могут «плавать» в жидкости как единый организм.",
    "У морских коньков самцы вынашивают потомство.",
    "Человеческий нос может различать до 1 триллиона запахов.",
    "Мозг продолжает работать 5–10 минут после смерти.",
    "Бананы светятся в ультрафиолете.",
    "У жирафов чёрный язык длиной до 45 см.",
    "Моллюск геодак может жить более 160 лет.",
    "Акулы чувствуют кровь на расстоянии до 5 км.",
    "Пчела может летать со скоростью до 25 км/ч.",
    "Вода может существовать одновременно в 3 состояниях.",
    "Планктон производит около 50% кислорода на Земле.",
    "Сердце креветки находится в голове.",
    "Некоторые виды рыб могут менять пол в течение жизни.",
    "Одна капля воды содержит 1.5 секстиллиона молекул.",
    "Киты поют сложные «песни» для общения на сотни км.",
    "У змей нет век — они моргают с помощью чешуи.",
    "Скорпион может выжить неделю без головы.",
    "У крыс челюсти крепче, чем у акулы.",
    "Язык хамелеона в 2 раза длиннее его тела.",
    "Киви — птица, которая не умеет летать, но нюхает как собака.",
    "Бактерия Deinococcus radiodurans переживает ядерный взрыв.",
    "У ленивца пищеварение занимает до месяца.",
    "Паук может вырабатывать 7 видов паутины одновременно.",
    "У человека при рождении 300 костей, во взрослом возрасте — 206.",
    "Некоторые деревья могут «спать» по ночам.",
    "Птеродактили жили ближе к нам по времени, чем к динозаврам.",
    "Медузы бессмертны... почти.",
    "В древнем Египте кошки были под защитой закона.",
    "Курицы могут запоминать до 100 лиц.",
    "Фотон может существовать миллионы лет — до взаимодействия.",
    "Ртуть — единственный металл, жидкий при комнатной температуре.",
    "У китов есть акцент в пении, как у людей в речи.",
    "Одна чайная ложка нейтронной звезды весила бы 6 миллиардов тонн.",
    "Мозг использует 20% всей энергии тела.",
    "Глаза страуса больше, чем его мозг.",
    "Во сне мы временно парализованы — это защита от движений."
]

async def send_random_fact(update: Update):
    await update.message.reply_text(random.choice(facts))

# Озвучка ответа через edge-tts
async def send_voice(update: Update, text: str):
    try:
        filename = f"voice_{update.effective_user.id}.mp3"
        communicate = edge_tts.Communicate(text, voice="ru-RU-DmitryNeural")
        await communicate.save(filename)
        with open(filename, "rb") as voice_file:
            await update.message.chat.send_action(action=ChatAction.UPLOAD_VOICE)
            await update.message.reply_voice(voice=voice_file)
        os.remove(filename)
    except Exception as e:
        print("❌ Ошибка при создании голосового сообщения:", e)
        await update.message.reply_text("⚠️ Не удалось озвучить ответ.")

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    await update.message.chat.send_action(ChatAction.TYPING)

    if user_message == "🧠 Задать вопрос":
        await update.message.reply_text("✍️ Напиши вопрос.")
        return
    elif user_message == "📚 Интересный факт":
        await send_random_fact(update)
        return
    elif user_message == "📝 Мои заметки":
        await show_notes(update, context)
        return
    elif user_message == "⏰ Напоминание":
        await update.message.reply_text("⏰ Введи: /remind 60 Напоминание через 1 минуту", parse_mode="Markdown")
        return
    elif user_message == "ℹ️ Помощь":
        await help_command(update, context)
        return
    elif user_message == "📩 Связь с владельцем":
        await update.message.reply_text("📬 Напиши [@pauelky](https://t.me/pauelky) — это мой создатель! Он всегда рад помочь.", parse_mode="Markdown")
        return
    elif user_message == "🔊 Ответ голосом":
        user_voice_mode[user_id] = True
        await update.message.reply_text("🎤 Напиши вопрос, я озвучу ответ голосом!")
        return

    if user_id not in user_histories:
        user_histories[user_id] = [
            {"role": "system", "content": "Ты умный Telegram-бот и всегда отвечаешь на русском языке. Отвечай дружелюбно и понятно."}
        ]
    user_histories[user_id].append({"role": "user", "content": user_message})
    if len(user_histories[user_id]) > 20:
        user_histories[user_id] = [user_histories[user_id][0]] + user_histories[user_id][-19:]

    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://t.me/username_pasha_Bot",
            "X-Title": "gpt-telegram-bot"
        }
        payload = {
            "model": "openai/gpt-3.5-turbo",
            "messages": user_histories[user_id]
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            print("📡 Отправка запроса в OpenRouter...")
            response = await client.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
            print("✅ Ответ получен:", response.status_code)
            result = response.json()
            reply = result["choices"][0]["message"]["content"]
            user_histories[user_id].append({"role": "assistant", "content": reply})

            # 🎤 Ответ голосом
            if user_voice_mode.get(user_id):
                await send_voice(update, reply)
                user_voice_mode[user_id] = False
            else:
                await update.message.reply_text(reply)
    except Exception as e:
        print("❌ Ошибка:", e)
        await update.message.reply_text("⚠️ Не удалось получить ответ от OpenRouter.")

# Заметки
async def add_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    note_text = " ".join(context.args)
    if not note_text:
        await update.message.reply_text("📝 Используй: /note Текст заметки", parse_mode="Markdown")
        return
    user_notes.setdefault(user_id, []).append(note_text)
    await update.message.reply_text("✅ Заметка сохранена!")

async def show_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    notes = user_notes.get(user_id, [])
    if not notes:
        await update.message.reply_text("📭 У тебя нет заметок.")
    else:
        await update.message.reply_text("📝 Твои заметки:\n" + "\n".join(f"• {note}" for note in notes))

# Напоминания
async def remind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        delay = int(context.args[0])
        text = " ".join(context.args[1:])
        await update.message.reply_text(f"⏰ Напоминание через {delay} сек.")
        await asyncio.sleep(delay)
        await update.message.reply_text(f"🔔 Напоминаю: {text}")
    except:
        await update.message.reply_text("❗️ Используй: /remind 10 Выйти на улицу", parse_mode="Markdown")

# ▶️ Запуск
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("note", add_note))
    app.add_handler(CommandHandler("remind", remind))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()  