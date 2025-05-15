import logging
from datetime import datetime, timezone
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ConversationHandler,
    CallbackContext
)
from api.kudago import fetch_kudago_events
from config import TELEGRAM_TOKEN

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния диалога
SELECT_CITY, SELECT_CATEGORY, SELECT_EVENT = range(3)

# Категории событий
CATEGORIES = {
    "🎵 Концерты": "concert",
    "🎭 Театры": "theater",
    "🖼 Выставки": "exhibition",
    "🎪 Фестивали": "festival"
}

# Города
CITIES = {
    "Москва": "msk",
    "Санкт-Петербург": "spb",
    "Казань": "kzn"
}


def get_back_button():
    """Кнопка 'Назад'"""
    return [InlineKeyboardButton("🔙 Назад", callback_data="back")]


def shorten_text(text, max_length=25):
    """Сокращает текст для кнопки"""
    if len(text) > max_length:
        return text[:max_length - 3] + "..."
    return text


async def start(update: Update, context: CallbackContext):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "🎉 Добро пожаловать в бот для поиска событий!\n"
        "Выберите город:",
        reply_markup=ReplyKeyboardMarkup(
            [[city] for city in CITIES.keys()],
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )
    return SELECT_CITY


async def select_city(update: Update, context: CallbackContext):
    """Обработка выбора города"""
    city = update.message.text
    if city not in CITIES:
        await update.message.reply_text("Пожалуйста, выберите город из списка:")
        return SELECT_CITY

    context.user_data['city'] = city
    context.user_data['current_state'] = SELECT_CATEGORY
    await update.message.reply_text(
        "Выберите категорию событий:",
        reply_markup=ReplyKeyboardMarkup(
            [[cat] for cat in CATEGORIES.keys()],
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )
    return SELECT_CATEGORY


async def select_category(update: Update, context: CallbackContext):
    """Обработка выбора категории"""
    category = update.message.text
    if category not in CATEGORIES:
        await update.message.reply_text("Пожалуйста, выберите категорию из списка:")
        return SELECT_CATEGORY

    context.user_data['category'] = category
    context.user_data['current_state'] = SELECT_EVENT
    city = CITIES[context.user_data['city']]
    events = fetch_kudago_events(city, CATEGORIES[category])

    if not events:
        await update.message.reply_text("😔 Событий не найдено")
        return SELECT_CATEGORY

    context.user_data['events'] = events[:10]  # Сохраняем до 10 событий

    # Создаем кнопки с названиями событий (сокращенными)
    buttons = [
        [InlineKeyboardButton(
            f"{shorten_text(event['title'])}",
            callback_data=str(idx)
        )]
        for idx, event in enumerate(events[:10])
    ]
    buttons.append(get_back_button())

    await update.message.reply_text(
        "Выберите событие:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return SELECT_EVENT


async def show_event(update: Update, context: CallbackContext):
    """Показ выбранного события"""
    query = update.callback_query
    await query.answer()

    if query.data == "back":
        return await back_handler(update, context)

    event_idx = int(query.data)
    event = context.user_data['events'][event_idx]

    # Форматируем дату
    date_str = "Дата не указана"
    if event.get('dates') and isinstance(event['dates'][0], dict):
        try:
            timestamp = event['dates'][0].get('start')
            if timestamp:
                dt = datetime.fromtimestamp(timestamp, tz=timezone.utc).replace(tzinfo=None)
                months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                          'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
                date_str = f"{dt.day} {months[dt.month - 1]} {dt.year}, {dt.hour}:{dt.minute:02d}"
        except Exception as e:
            logger.error(f"Ошибка форматирования даты: {e}")
            date_str = f"Скоро ({timestamp})"

    # Формируем текст
    text = f"🎤 *{event.get('title', 'Без названия')}*\n\n"

    if event.get('place'):
        text += f"🏠 *Место:* {event['place'].get('name', 'Не указано')}\n"

    text += f"📅 *Дата:* {date_str}\n"

    if event.get('price'):
        text += f"💵 *Цена:* {event['price']}\n"

    if event.get('description'):
        text += f"\nℹ️ *Описание:*\n{event['description'][:300]}...\n"

    # Создаем кнопки
    buttons = []
    if event.get('site_url'):
        buttons.append([InlineKeyboardButton("🎟️ Купить билет", url=event['site_url'])])

    """Добавляется кнопка назад"""
    buttons.append(get_back_button())

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )
    return SELECT_EVENT


async def back_handler(update: Update, context: CallbackContext):
    """Обработка кнопки 'Назад'"""
    query = update.callback_query
    await query.answer()

    current_state = context.user_data.get('current_state', SELECT_CITY)

    if current_state == SELECT_EVENT:
        # Возвращаемся к выбору категории
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="Выберите категорию событий:",
            reply_markup=ReplyKeyboardMarkup(
                [[cat] for cat in CATEGORIES.keys()],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        await query.message.delete()
        return SELECT_CATEGORY
    elif current_state == SELECT_CATEGORY:
        # Возвращаемся к выбору города
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="Выберите город:",
            reply_markup=ReplyKeyboardMarkup(
                [[city] for city in CITIES.keys()],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        await query.message.delete()
        return SELECT_CITY


async def cancel(update: Update, context: CallbackContext):
    """Отмена диалога"""
    await update.message.reply_text(
        "Диалог завершен. Нажмите /start чтобы начать заново.",
        reply_markup=ReplyKeyboardMarkup([["/start"]], resize_keyboard=True)
    )
    return ConversationHandler.END


def main():
    """Запуск бота"""
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECT_CITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, select_city)
            ],
            SELECT_CATEGORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, select_category)
            ],
            SELECT_EVENT: [
                CallbackQueryHandler(show_event),
                CallbackQueryHandler(back_handler, pattern="^back$")
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )

    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == '__main__':
    main()