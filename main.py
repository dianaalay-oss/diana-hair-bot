# -*- coding: utf-8 -*-

import telebot
from groq import Groq

BOT_TOKEN = "8727973525:AAGrKB0AF0U7O9gu71YZCnWip7gd7l8mPk8"
GROQ_API_KEY = "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"
ADMIN_ID = 5051521828
WHATSAPP_LINK = "https://wa.me/972507813306"

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

users = {}

TEXTS = {
    "ru": {
        "welcome": (
            "Здравствуйте 🌿\n"
            "Я AI-консультант *Diana Hair AI*.\n\n"
            "Я помогу разобрать состояние кожи головы и волос по фото и ответам.\n\n"
            "💳 *Стоимость AI-консультации — 50 ₪*\n"
            "👩‍⚕️ Личная консультация с Дианой — 250 ₪\n\n"
            "Для оплаты переведите 50 ₪ на:\n"
            "📱 *PayBox / Bit:* +972507813306\n\n"
            "После оплаты нажмите кнопку 👇"
        ),
        "paid_btn": "✅ Я оплатил(а)",
        "wait_confirm": "⏳ Ожидайте подтверждения оплаты.",
        "confirmed": "✅ Оплата подтверждена! Начинаем консультацию.",
        "rejected": "❌ Оплата не найдена. Попробуйте снова.",
        "question_label": "Вопрос",
        "of": "из",
        "photo_scalp": "📸 Загрузите фото кожи головы",
        "photo_length": "📸 Загрузите фото длины волос",
        "generating": "⏳ Анализирую данные…",
        "wa_btn": "💬 Написать Диане в WhatsApp",
        "restart_btn": "🔄 Начать заново",
        "offer": "💆‍♀️ Хотите личный разбор с Дианой?\n\nОнлайн или очно в Израиле — 250 ₪",
        "questions": [
            "Сколько вам лет?",
            "Что беспокоит больше всего?",
            "Как давно существует проблема?",
            "Есть ли зуд кожи головы?",
            "Есть ли перхоть?",
            "Есть ли жирность кожи головы?",
            "Есть ли выпадение волос?",
            "Были ли роды, стресс или болезнь за последние месяцы?",
            "Как часто вы моете голову?",
            "Красите ли вы волосы?",
            "Какие средства используете сейчас?",
            "Есть ли анализы крови? Если да — опишите показатели.",
        ],
        "system_prompt": (
            "Ты AI-консультант по трихологии Diana Hair AI. "
            "Не ставь медицинские диагнозы. Дай информационные рекомендации. "
            "Составь консультацию на русском языке: причины, состояние кожи головы, "
            "состояние волос, план ухода на 30 дней, средства, где купить, когда идти к врачу. "
            "Тон профессиональный, теплый, премиальный."
        ),
    }
}


def t(uid, key):
    lang = users.get(uid, {}).get("lang", "ru")
    return TEXTS[lang][key]


def total_questions(uid):
    return len(t(uid, "questions")) + 2


@bot.message_handler(commands=["start"])
def start(message):
    uid = message.chat.id
    users[uid] = {"step": "await_payment", "answers": [], "photos": [], "lang": "ru"}

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton(t(uid, "paid_btn")))

    bot.send_message(uid, t(uid, "welcome"), parse_mode="Markdown", reply_markup=markup)


@bot.message_handler(func=lambda m: users.get(m.chat.id, {}).get("step") == "await_payment")
def payment_claimed(message):
    uid = message.chat.id

    if message.text != t(uid, "paid_btn"):
        return

    users[uid]["step"] = "await_confirm"

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_{uid}"),
        telebot.types.InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{uid}")
    )

    bot.send_message(
        ADMIN_ID,
        f"💰 Новая оплата!\nИмя: {message.from_user.first_name}\nID: {uid}",
        reply_markup=markup
    )

    bot.send_message(uid, t(uid, "wait_confirm"), reply_markup=telebot.types.ReplyKeyboardRemove())


@bot.callback_query_handler(func=lambda c: c.data.startswith("confirm_"))
def confirm_payment(call):
    uid = int(call.data.split("_")[1])
    users[uid]["step"] = 0
    bot.send_message(uid, t(uid, "confirmed"))
    ask_question(uid)
    bot.answer_callback_query(call.id, "✅")


@bot.callback_query_handler(func=lambda c: c.data.startswith("reject_"))
def reject_payment(call):
    uid = int(call.data.split("_")[1])
    users[uid]["step"] = "await_payment"

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton(t(uid, "paid_btn")))

    bot.send_message(uid, t(uid, "rejected"), reply_markup=markup)
    bot.answer_callback_query(call.id, "❌")


def ask_question(uid):
    step = users[uid]["step"]
    questions = t(uid, "questions")
    total = total_questions(uid)

    if step < len(questions):
        bot.send_message(
            uid,
            f"*{t(uid, 'question_label')} {step + 1} {t(uid, 'of')} {total}*\n\n{questions[step]}",
            parse_mode="Markdown"
        )
    elif step == len(questions):
        bot.send_message(uid, t(uid, "photo_scalp"))
    elif step == len(questions) + 1:
        bot.send_message(uid, t(uid, "photo_length"))


@bot.message_handler(content_types=["text"])
def collect_answers(message):
    uid = message.chat.id

    if uid not in users:
        start(message)
        return

    if message.text == t(uid, "restart_btn"):
        restart(message)
        return

    if not isinstance(users[uid].get("step"), int):
        return

    step = users[uid]["step"]
    questions = t(uid, "questions")

    if step < len(questions):
        users[uid]["answers"].append(f"Q: {questions[step]}\nA: {message.text}")
        users[uid]["step"] += 1
        ask_question(uid)


@bot.message_handler(content_types=["photo"])
def collect_photos(message):
    uid = message.chat.id

    if uid not in users or not isinstance(users[uid].get("step"), int):
        return

    step = users[uid]["step"]
    questions = t(uid, "questions")

    if step == len(questions):
        users[uid]["photos"].append("фото кожи головы получено")
        users[uid]["step"] += 1
        ask_question(uid)
    elif step == len(questions) + 1:
        users[uid]["photos"].append("фото длины волос получено")
        users[uid]["step"] = "generating"
        generate_consultation(uid)


def generate_consultation(uid):
    bot.send_message(uid, t(uid, "generating"))

    answers_text = "\n".join(users[uid]["answers"])

    prompt = (
        f"Данные клиента:\n{answers_text}\n\n"
        f"Фото: {', '.join(users[uid]['photos'])}\n\n"
        f"Составь полную консультацию."
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": t(uid, "system_prompt")},
            {"role": "user", "content": prompt}
        ],
        max_tokens=2000
    )

    result = response.choices[0].message.content
    bot.send_message(uid, result)

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(t(uid, "wa_btn"), url=WHATSAPP_LINK))
    bot.send_message(uid, t(uid, "offer"), reply_markup=markup)

    restart_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    restart_markup.add(telebot.types.KeyboardButton(t(uid, "restart_btn")))
    bot.send_message(uid, "🔄", reply_markup=restart_markup)

    users[uid]["step"] = "done"


def restart(message):
    uid = message.chat.id
    users[uid] = {"step": "await_payment", "answers": [], "photos": [], "lang": "ru"}

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton(t(uid, "paid_btn")))

    bot.send_message(uid, t(uid, "welcome"), parse_mode="Markdown", reply_markup=markup)


bot.polling(none_stop=True)
