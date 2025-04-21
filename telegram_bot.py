import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackContext
)
import requests
from config import TELEGRAM_TOKEN  # Создайте config.py с токеном
from database.crud import get_user, update_user_city
from api.event_providers import get_events
from api.maps import generate_map_link

# Состояния для ConversationHandler
CITY, COMMAND = range(2)

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def get_events_from_api(city, category):
    response = requests.post(
        'http://localhost:5000/api/events',
        json={'city': city, 'category': category}
    )
    return response.json()


async def start(update: Update, context: CallbackContext):
    """Обработчик команды /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}! Я бот для поиска событий.\n"
        "Введите город, где искать события:"
    )
    return CITY


async def set_city(update: Update, context: CallbackContext):
    """Сохраняем город и спрашиваем команду"""
    city = update.message.text
    context.user_data['city'] = city

    reply_keyboard = [["Концерты", "Выставки", "Фестивали"]]
    await update.message.reply_text(
        "Что ищем?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return COMMAND


async def find_events(update: Update, context: CallbackContext):
    """Поиск событий и отправка результата"""
    category = update.message.text.lower()
    city = context.user_data.get('city')

    if not city:
        await update.message.reply_text("Сначала укажите город!")
        return CITY

    try:
        events = get_events_from_api(city=city, category=category)
        if not events:
            await update.message.reply_text("Ничего не найдено 😔")
            return COMMAND

        # Отправляем первое событие
        event = events[0]
        text = (
            f"🎤 {event['title']}\n"
            f"📍 {event['place']['name']}\n"
            f"📅 {event['dates'][0]}\n"
            f"💵 {event.get('price', '?')} руб."
        )

        # Генерируем карту
        map_url = generate_map_link([event])

        await update.message.reply_photo(
            photo=map_url,
            caption=text
        )

    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("Ошибка при поиске событий. Попробуйте позже.")

    return COMMAND


async def cancel(update: Update, context: CallbackContext):
    """Отмена диалога"""
    await update.message.reply_text("Поиск отменён.")
    return ConversationHandler.END


def main():
    """Запуск бота"""
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_city)],
            COMMAND: [MessageHandler(filters.TEXT & ~filters.COMMAND, find_events)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == '__main__':
    main()