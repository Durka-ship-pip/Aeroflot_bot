import telebot
import os
import re
import csv
import json
from datetime import datetime

# === CONFIG ===
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 8050560759
bot = telebot.TeleBot(TOKEN)

CSV_FILE = "applications.csv"
CSV_ALL_FILE = "historyanket.csv"
VACANCY_FILE = "vacancies.json"

user_state = {}
user_data = {}


# === ВАКАНСИИ ===
def load_vacancies():
    if os.path.exists(VACANCY_FILE):
        try:
            with open(VACANCY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Ошибка при загрузке {VACANCY_FILE}: {e}")
    return {
        "🧑‍✈️ Пилот": True,
        "🎧 Диспетчер": True,
        "✈️ Стюард": True,
        "🛠 Наземная служба": True
    }


def save_vacancies():
    with open(VACANCY_FILE, "w", encoding="utf-8") as f:
        json.dump(vacancy_status, f, ensure_ascii=False, indent=2)


vacancy_status = load_vacancies()


# === МЕНЮ ===
def show_main_menu(chat_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton("✈️ Сотрудничество")
    btn2 = telebot.types.KeyboardButton("👨‍✈️ Набор в команду")
    btn3 = telebot.types.KeyboardButton("🗂 Проверить статус анкеты")
    markup.add(btn1, btn2)
    markup.add(btn3)
    bot.send_message(chat_id, "Привет я бот Аэрофлот! Для чего ты сюда пришёл?", reply_markup=markup)
    user_state[chat_id] = None
    user_data[chat_id] = {}


# === START ===
@bot.message_handler(commands=['start'])
def start(message):
    show_main_menu(message.chat.id)


# === ПРОВЕРКА СТАТУСА АНКЕТЫ ===
def get_user_status(user_id):
    if not os.path.exists(CSV_ALL_FILE):
        return None
    with open(CSV_ALL_FILE, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if len(row) >= 14 and str(row[2]) == str(user_id):
                return row[13]
    return None


@bot.message_handler(func=lambda msg: msg.text == "🗂 Проверить статус анкеты")
def check_status(message):
    status = get_user_status(message.chat.id)
    if not status:
        bot.send_message(message.chat.id, "🕵️ Мы не нашли вашу анкету.")
    elif "Принята" in status:
        bot.send_message(message.chat.id, "✅ Ваша анкета *принята!*", parse_mode="Markdown")
    elif "Отклонена" in status:
        bot.send_message(message.chat.id, "❌ Ваша анкета *отклонена!*", parse_mode="Markdown")
    elif "Собеседование" in status:
        bot.send_message(message.chat.id, f"📅 Ваше собеседование назначено: *{status.split(': ')[1]}*", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "⚙️ Ваша анкета *на рассмотрении*.", parse_mode="Markdown")


# === СОХРАНЕНИЕ АНКЕТ ===
def save_to_csv(message):
    data = user_data.get(message.chat.id, {})
    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    # активные
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, "a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "Тип", "Имя", "ID", "Username", "Возраст", "Авиакомпания", "Вакансия", "Страна", "GMT",
                "Подписчики", "Телеграм-канал", "TikTok", "Телефон", "Статус"
            ])
        writer.writerow([
            data.get("type", "—"),
            message.from_user.first_name,
            message.chat.id,
            f"@{message.from_user.username}" if message.from_user.username else "—",
            data.get("age", "—"),
            data.get("airline", "—"),
            data.get("vacancy", "—"),
            data.get("country", "—"),
            data.get("gmt", "—"),
            data.get("followers", "—"),
            data.get("telegram_channel", "—"),
            data.get("tiktok", "—"),
            data.get("phone", "—"),
            "Ожидает"
        ])

    # история
    file_all_exists = os.path.isfile(CSV_ALL_FILE)
    with open(CSV_ALL_FILE, "a", newline='', encoding="utf-8") as f_all:
        writer_all = csv.writer(f_all)
        if not file_all_exists:
            writer_all.writerow([
                "Тип", "Имя", "ID", "Username", "Возраст", "Авиакомпания", "Вакансия", "Страна", "GMT",
                "Подписчики", "Телеграм-канал", "TikTok", "Телефон", "Статус", "Дата заполнения"
            ])
        writer_all.writerow([
            data.get("type", "—"),
            message.from_user.first_name,
            message.chat.id,
            f"@{message.from_user.username}" if message.from_user.username else "—",
            data.get("age", "—"),
            data.get("airline", "—"),
            data.get("vacancy", "—"),
            data.get("country", "—"),
            data.get("gmt", "—"),
            data.get("followers", "—"),
            data.get("telegram_channel", "—"),
            data.get("tiktok", "—"),
            data.get("phone", "—"),
            "Ожидает",
            now
        ])


# === ОТПРАВКА АНКЕТЫ АДМИНУ ===
def send_to_admin(message):
    data = user_data.get(message.chat.id, {})
    text = (
        f"📝 Новая анкета ({data.get('type', '—')})\n\n"
        f"👤 Пользователь: {message.from_user.first_name}\n"
        f"🆔 ID: {message.chat.id}\n"
        f"🔗 Username: @{message.from_user.username if message.from_user.username else '—'}\n"
        f"📋 Возраст: {data.get('age', '—')}\n"
        f"✈️ Авиакомпания: {data.get('airline', '—')}\n"
        f"📍 Страна: {data.get('country', '—')}\n"
        f"🕒 GMT: {data.get('gmt', '—')}\n"
        f"📞 Телефон: {data.get('phone', '—')}\n"
        f"💼 Вакансия: {data.get('vacancy', '—')}\n"
    )
    bot.send_message(ADMIN_ID, text)


# === ОБНОВЛЕНИЕ СТАТУСОВ ===
def update_status(user_id, status):
    for file_path in [CSV_FILE, CSV_ALL_FILE]:
        if not os.path.exists(file_path):
            continue
        rows = []
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            for row in reader:
                if len(row) > 2 and str(row[2]) == str(user_id):
                    if len(row) >= 14:
                        row[13] = status
                    else:
                        row.append(status)
                rows.append(row)
        with open(file_path, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            if headers:
                writer.writerow(headers)
            writer.writerows(rows)
    if status.startswith("Принята") or status.startswith("Отклонена"):
        remove_from_active(user_id)


def remove_from_active(user_id):
    if not os.path.exists(CSV_FILE):
        return
    rows = []
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader, None)
        for row in reader:
            if len(row) > 2 and str(row[2]) != str(user_id):
                rows.append(row)
    with open(CSV_FILE, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        if headers:
            writer.writerow(headers)
        writer.writerows(rows)


# === BACK BUTTON ===
def back_button():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton("🔙 Назад в меню"))
    return markup


# === КОМАНДЫ АДМИНА ===
# /accept, /decline, /msg, /interview, /getcsv, /gethistory, /clearcsv, /vacno, /vacancies, /closevacancy, /openvacancy, /resetvacancies
# (в следующем сообщении я отправлю вторую часть — все команды админа, чтобы не обрезалось)
# ===== Команды администратора =====

# --- Принять анкету ---
@bot.message_handler(commands=['accept'])
def accept_user(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "⛔ Только администратор может это делать.")
    parts = message.text.split()
    if len(parts) < 2:
        return bot.reply_to(message, "Используй формат: /accept <user_id>")
    try:
        user_id = int(parts[1])
        bot.send_message(user_id, "✅ Здравствуйте! Ваша анкета одобрена. Мы скоро свяжемся с вами ✈️")
        update_status(user_id, "Принята")
        bot.reply_to(message, f"✅ Анкета пользователя {user_id} принята и обновлена.")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")


# --- Отклонить анкету ---
@bot.message_handler(commands=['decline'])
def decline_user(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "⛔ Только администратор может это делать.")
    parts = message.text.split()
    if len(parts) < 2:
        return bot.reply_to(message, "Используй формат: /decline <user_id>")
    try:
        user_id = int(parts[1])
        text = ("Здравствуйте, ваша анкета отклонена! ❌\n\n"
                "Если вы думаете, что это ошибка — напишите в поддержку:\n"
                "@Aeroflotprojectflight_support")
        bot.send_message(user_id, text)
        update_status(user_id, "Отклонена")
        bot.reply_to(message, f"🚫 Анкета пользователя {user_id} отклонена.")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")


# --- Отправить сообщение ---
@bot.message_handler(commands=['msg'])
def admin_msg(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "⛔ Только администратор может это делать.")
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        return bot.reply_to(message, "Формат: /msg <user_id> <текст>")
    try:
        user_id = int(parts[1])
        text_to_send = parts[2]
        bot.send_message(user_id, f"📩 Сообщение от администрации:\n\n{text_to_send}")
        bot.reply_to(message, f"✅ Сообщение отправлено пользователю {user_id}")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")


# --- Назначить собеседование ---
@bot.message_handler(commands=['interview'])
def interview_user(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "⛔ Только администратор может это делать.")
    parts = message.text.split()
    if len(parts) < 3:
        return bot.reply_to(message, "Используй формат: /interview <user_id> <дата>")
    try:
        user_id = int(parts[1])
        date = parts[2]
        bot.send_message(user_id,
                         f"Здравствуйте! Ваша анкета была рассмотрена ✅\n\n"
                         f"Ваше собеседование назначено на **{date}**.\n\n"
                         "Если вам неудобно, напишите: «Я хочу поменять собеседование ДД.ММ».",
                         parse_mode="Markdown")
        update_status(user_id, f"Собеседование: {date}")
        bot.reply_to(message, f"📅 Собеседование назначено пользователю {user_id} на {date}.")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")


# --- Вакансия недоступна ---
@bot.message_handler(commands=['vacno'])
def vacancy_unavailable(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "⛔ Только администратор может это делать.")
    parts = message.text.split()
    if len(parts) < 2:
        return bot.reply_to(message, "Формат: /vacno <user_id>")
    try:
        user_id = int(parts[1])
        old_vacancy = user_data.get(user_id, {}).get("vacancy")
        bot.send_message(user_id, "❌ Данная вакансия занята. Просим вас выбрать другую.")
        # Меню без старой вакансии
        vacancies = ["🧑‍✈️ Пилот", "🎧 Диспетчер", "✈️ Стюард", "🛠 Наземная служба"]
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        for v in vacancies:
            if v != old_vacancy:
                markup.add(telebot.types.KeyboardButton(v))
        markup.add(telebot.types.KeyboardButton("🔙 Назад в меню"))
        bot.send_message(user_id, "Пожалуйста, выберите другую вакансию:", reply_markup=markup)
        if user_id in user_data:
            user_data[user_id]["vacancy"] = None
        user_state[user_id] = "team_country"
        bot.reply_to(message, f"✅ Пользователь {user_id} возвращён к выбору вакансии.")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")


# --- Скачать активные анкеты ---
@bot.message_handler(commands=['getcsv'])
def get_csv(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "⛔ Только администратор может это делать.")
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "rb") as f:
            bot.send_document(ADMIN_ID, f, caption="📄 Активные анкеты")
        os.remove(CSV_FILE)
        bot.send_message(ADMIN_ID, "✅ Файл applications.csv очищен после отправки.")
    else:
        bot.reply_to(message, "❌ Файл отсутствует.")


# --- Скачать всю историю анкет ---
@bot.message_handler(commands=['gethistory'])
def get_history(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "⛔ Только администратор может это делать.")
    if os.path.exists(CSV_ALL_FILE):
        with open(CSV_ALL_FILE, "rb") as f:
            bot.send_document(ADMIN_ID, f, caption="📜 Полная история анкет (historyanket.csv)")
    else:
        bot.reply_to(message, "❌ История отсутствует.")


# --- Очистить активные анкеты ---
@bot.message_handler(commands=['clearcsv'])
def clear_csv(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "⛔ Только администратор может это делать.")
    if not os.path.exists(CSV_FILE):
        return bot.reply_to(message, "Файл уже пуст.")
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader, None)
    with open(CSV_FILE, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        if headers:
            writer.writerow(headers)
    bot.send_message(ADMIN_ID, "🧹 Все активные анкеты очищены. История сохранена.")


# --- Управление вакансиями ---
@bot.message_handler(commands=['vacancies'])
def list_vacancies(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "⛔ Только администратор может это делать.")
    text = "📋 *Текущие вакансии:*\n\n"
    for vac, avail in vacancy_status.items():
        text += f"{vac} — {'✅ Открыта' if avail else '🚫 Закрыта'}\n"
    bot.send_message(ADMIN_ID, text, parse_mode="Markdown")


@bot.message_handler(commands=['closevacancy'])
def close_vacancy(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "⛔ Только администратор может это делать.")
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return bot.reply_to(message, "Формат: /closevacancy <название>")
    name = parts[1].strip()
    for vac in vacancy_status:
        if name.lower() in vac.lower():
            vacancy_status[vac] = False
            save_vacancies()
            return list_vacancies(message)
    bot.reply_to(message, "❌ Вакансия не найдена.")


@bot.message_handler(commands=['openvacancy'])
def open_vacancy(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "⛔ Только администратор может это делать.")
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return bot.reply_to(message, "Формат: /openvacancy <название>")
    name = parts[1].strip()
    for vac in vacancy_status:
        if name.lower() in vac.lower():
            vacancy_status[vac] = True
            save_vacancies()
            return list_vacancies(message)
    bot.reply_to(message, "❌ Вакансия не найдена.")


@bot.message_handler(commands=['resetvacancies'])
def reset_vacancies(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "⛔ Только администратор может это делать.")
    for vac in vacancy_status:
        vacancy_status[vac] = True
    save_vacancies()
    bot.send_message(ADMIN_ID, "🔄 Все вакансии снова открыты.")
    list_vacancies(message)


# === ЗАПУСК ===
bot.polling(non_stop=True)
