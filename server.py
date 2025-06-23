import os
import threading
from dotenv import load_dotenv
import telebot
from flask import Flask, request, jsonify
import json

# Загрузка переменных окружения
load_dotenv(override=True)
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
API_KEY = os.getenv('API_KEY') 

app = Flask(__name__)
bot = telebot.TeleBot(TOKEN)

# Функция загрузки словаря чатов
def load_user_chats():
    if not os.path.exists('data.json'):
        return {}
    else:
        with open('data.json', 'r') as f:
            return json.load(f)

# Словарь для хранения chat_id пользователей
user_chats = load_user_chats()

# Функция сохранения словаря чатов
def save_user_chats():
    with open('data.json', 'w') as f:
        json.dump(user_chats, f)

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    user_chats[str(user_id)] = chat_id  # сохраняем как строку для совместимости с JSON
    save_user_chats()
    bot.reply_to(message, f"Вы успешно зарегистрированы! Ваш ID: {user_id}.")

# Обработчик команды /ready для оповещения о готовности авто
@bot.message_handler(commands=['ready'])
def handle_ready(message):
    user_id = str(message.from_user.id)
    chat_id = message.chat.id

    # Проверка, зарегистрирован ли пользователь
    if user_id not in user_chats:
        bot.reply_to(message, "Пожалуйста, сначала зарегистрируйтесь командой /start.")
        return

    # Отправляем сообщение о готовности авто
    try:
        bot.send_message(chat_id=user_chats[user_id], text="Ваш автомобиль готов! Можете забирать его из сервиса.")
        bot.reply_to(message, "Уведомление о готовности отправлено.")
    except Exception as e:
        bot.reply_to(message, f"Ошибка при отправке уведомления: {str(e)}")

# Обработчик текстовых сообщений (по умолчанию)
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    bot.reply_to(message, "Отправьте /start для регистрации или /ready для получения уведомления о готовности авто.")

# API endpoint для отправки уведомлений (например, из административной системы)
@app.route('/send_notification', methods=['POST'])
def send_notification():
    # Проверка API ключа
    if request.headers.get('X-API-KEY') != API_KEY:
        return jsonify({"status": "error", "message": "Invalid API key"}), 403
    
    data = request.json
    user_id = str(data.get('user_id'))
    message_text = data.get('message')
    print(user_id)
    
    if not user_id or not message_text:
        return jsonify({"status": "error", "message": "Missing user_id or message"}), 400
    
    if user_id not in user_chats:
        return jsonify({"status": "error", "message": "User not found"}), 404
    
    try:
        bot.send_message(chat_id=user_chats[user_id], text=message_text)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Функция для запуска бота в отдельном потоке
def run_bot():
    print("Бот запущен...")
    load_user_chats()
    bot.infinity_polling()

if __name__ == '__main__':
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    
    # Запускаем Flask сервер для API
    app.run(host='0.0.0.0', port=5050)