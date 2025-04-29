import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackContext
)
import pprint
from api.kudago import fetch_kudago_events
from config import TELEGRAM_TOKEN

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
CITY, CATEGORY = range(2)

# Категории событий
CATEGORIES = {
    "🎵 Концерты": "concert",
    "🎭 Театры": "theater",
    "🖼 Выставки": "exhibition",
    "🎪 Фестивали": "festival",
    "🎬 Кино": "cinema",
    "🍹 Вечеринки": "party",
    "👶 Детям": "kids"
}

# Маппинг городов
CITY_MAPPING = {
    "Москва": "msk",
    "Санкт-Петербург": "spb",
    "Новосибирск": "nsk",
    "Екатеринбург": "ekb",
    "Казань": "kzn"
}


async def start(update: Update, context: CallbackContext):
    """Обработчик команды /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}! Я помогу найти интересные события.\n"
        "Выберите город:",
        reply_markup=ReplyKeyboardMarkup(
            [[city] for city in CITY_MAPPING.keys()],
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )
    return CITY


async def select_city(update: Update, context: CallbackContext):
    """Обработчик выбора города"""
    city = update.message.text
    if city not in CITY_MAPPING:
        await update.message.reply_text("Пожалуйста, выберите город из списка:")
        return CITY

    context.user_data['city'] = city
    await update.message.reply_text(
        "Выберите категорию событий:",
        reply_markup=ReplyKeyboardMarkup(
            [[category] for category in CATEGORIES.keys()],
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )
    return CATEGORY


async def show_events(update: Update, context: CallbackContext):
    """Показ событий по выбранной категории"""
    category_name = update.message.text
    if category_name not in CATEGORIES:
        await update.message.reply_text("Пожалуйста, выберите категорию из списка:")
        return CATEGORY

    city = context.user_data.get('city')
    category = CATEGORIES[category_name]

    await update.message.reply_text(f"🔍 Ищу {category_name.lower()} в {city}...")

    try:
        events = fetch_kudago_events(
            city=CITY_MAPPING[city],
            category=category,
            page_size=5
        )
        pprint.pprint(events)

        if not events:
            await update.message.reply_text("😔 Событий не найдено. Попробуйте другую категорию.")
            return CATEGORY

        for event in events:
            # Формируем описание события
            description = f"🎤 *{event['title']}*\n\n"

            if 'place' in event and event['place']:
                description += f"🏠 *Место:* {event['place']['id']}\n"
                if 'address' in event['place']:
                    description += f"📍 *Адрес:* {event['place']['address']}\n"

            if 'dates' in event and event['dates']:
                description += f"📅 *Дата:* {event['dates'][0]}\n"

            if 'price' in event and event['price']:
                description += f"💵 *Цена:* {event['price']}\n"

            # Создаем кнопку "Подробнее"
            keyboard = []
            if 'site_url' in event:
                keyboard.append([InlineKeyboardButton("🌐 Подробнее", url=event['site_url'])])

            # Отправляем сообщение

            await update.message.reply_text(
                    description,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("⚠️ Произошла ошибка. Пожалуйста, попробуйте позже.")

    return CATEGORY


async def cancel(update: Update, context: CallbackContext):
    """Отмена диалога"""
    await update.message.reply_text(
        "Поиск отменён. Нажмите /start чтобы начать заново.",
        reply_markup=ReplyKeyboardMarkup([["/start"]], resize_keyboard=True)
    )
    return ConversationHandler.END


async def error_handler(update: Update, context: CallbackContext):
    """Обработчик ошибок"""
    logger.error(f"Update {update} caused error {context.error}")
    await update.message.reply_text("⚠️ Произошла ошибка. Пожалуйста, попробуйте позже.")


def main():
    """Запуск бота"""
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_city)],
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, show_events)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)

    logger.info("Бот запущен")
    application.run_polling()


if __name__ == '__main__':
    main()