import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackContext
)
import pprint

from api.gpt4free.gpt import DialogGPT
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


class EventBot:
    # Состояния для ConversationHandler
    CITY, CATEGORY = range(2)

    def __init__(self, token: str):
        self.TELEGRAM_TOKEN = token
        self.logger = self._setup_logging()

        self.gptPrompt = None
        # Конфигурация данных
        self.CATEGORIES = {
            "🎵 Концерты": "concert",
            "🎭 Театры": "theater",
            "🖼 Выставки": "exhibition",
            "🎪 Фестивали": "festival",
            "🎬 Кино": "cinema",
            "🍹 Вечеринки": "party",
            "👶 Детям": "kids"
        }

        self.CITY_MAPPING = {
            "Москва": "msk",
            "Санкт-Петербург": "spb",
            "Новосибирск": "nsk",
            "Екатеринбург": "ekb",
            "Казань": "kzn"
        }

    @staticmethod
    def _setup_logging():
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )
        return logging.getLogger(__name__)

    async def start(self, update: Update, context: CallbackContext):
        """Обработчик команды /start"""
        user = update.effective_user

        self.gptPrompt = DialogGPT(update.effective_chat.id)

        await update.message.reply_text(
            f"Привет, {user.first_name}! Я помогу найти интересные события.\n"
            "Выберите город:",
            reply_markup=ReplyKeyboardMarkup(
                [[city] for city in self.CITY_MAPPING.keys()],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return self.CITY

    async def select_city(self, update: Update, context: CallbackContext):
        """Обработчик выбора города"""
        city = update.message.text
        if city not in self.CITY_MAPPING:
            await update.message.reply_text("Пожалуйста, выберите город из списка:")
            return self.CITY

        context.user_data['city'] = city
        await update.message.reply_text(
            "Выберите категорию событий:",
            reply_markup=ReplyKeyboardMarkup(
                [[category] for category in self.CATEGORIES.keys()],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return self.CATEGORY

    async def show_events(self, update: Update, context: CallbackContext):
        """Показ событий по выбранной категории"""
        category_name = update.message.text
        if category_name not in self.CATEGORIES:
            await update.message.reply_text("Пожалуйста, выберите категорию из списка:")
            return self.CATEGORY

        city = context.user_data.get('city')
        category = self.CATEGORIES[category_name]

        await update.message.reply_text(f"🔍 Ищу {category_name.lower()} в {city}...")

        try:
            events = fetch_kudago_events(
                city=self.CITY_MAPPING[city],
                category=category,
                page_size=5
            )

            if not events:
                await update.message.reply_text("😔 Событий не найдено. Попробуйте другую категорию.")
                return self.CATEGORY

            for event in events:
                description = f"🎤 *{event['title']}*\n\n"

                if 'place' in event and event['place']:
                    description += f"🏠 *Место:* {event['place']['id']}\n"
                    if 'address' in event['place']:
                        description += f"📍 *Адрес:* {event['place']['address']}\n"

                if 'dates' in event and event['dates']:
                    description += f"📅 *Дата:* {event['dates'][0]}\n"

                if 'price' in event and event['price']:
                    description += f"💵 *Цена:* {event['price']}\n"

                keyboard = []
                if 'site_url' in event:
                    keyboard.append([InlineKeyboardButton("🌐 Подробнее", url=event['site_url'])])

                await update.message.reply_text(
                    description,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )

        except Exception as e:
            self.logger.error(f"Error: {e}")
            await update.message.reply_text("⚠️ Произошла ошибка. Пожалуйста, попробуйте позже.")

        return self.CATEGORY

    async def cancel(self, update: Update, context: CallbackContext):
        """Отмена диалога"""
        await update.message.reply_text(
            "Поиск отменён. Нажмите /start чтобы начать заново.",
            reply_markup=ReplyKeyboardMarkup([["/start"]], resize_keyboard=True)
        )
        return ConversationHandler.END

    async def error_handler(self, update: Update, context: CallbackContext):
        """Обработчик ошибок"""
        self.logger.error(f"Update {update} caused error {context.error}")
        await update.message.reply_text("⚠️ Произошла ошибка. Пожалуйста, попробуйте позже.")

    async def gpt_talk(self, update: Update, context: CallbackContext):
        """Обработчик GPT-диалога"""
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING
        )
        try:
            answer = await self.gptPrompt.createDialog(update.message.text)
            print(answer + "0")
            await update.message.reply_text(answer)
        except TypeError:
            await self.error_handler()

    def run(self):
        """Запуск бота"""
        application = ApplicationBuilder().token(self.TELEGRAM_TOKEN).build()

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start)],
            states={
                self.CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.select_city)],
                self.CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.show_events)]
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )

        application.add_handler(conv_handler)
        application.add_error_handler(self.error_handler)
        application.add_handler(MessageHandler(filters.TEXT, self.gpt_talk))

        self.logger.info("Бот запущен")
        application.run_polling()


if __name__ == '__main__':
    bot = EventBot(TELEGRAM_TOKEN)
    bot.run()