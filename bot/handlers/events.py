"""
Обработчики для работы с событиями: создание, поиск, заявки.
"""

import asyncio
from datetime import datetime

from api_client import api_client
from common import format_event_text, format_user_info, get_sport_keyboard
from keyboards import get_main_menu_keyboard
from loguru import logger
from states import EventCreationStates
from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from utils import safe_callback, safe_handler


def register_events_handlers(bot: TeleBot):
    """
    Регистрация обработчиков событий.

    Args:
        bot: Экземпляр TeleBot
    """
    # Создаём декораторы для безопасной обработки ошибок
    safe = safe_handler(bot)
    safe_cb = safe_callback(bot)

    @bot.message_handler(func=lambda m: m.text == "➕ Создать тренировку")
    @safe
    def create_event_start(message: Message):
        """Начать создание события."""
        asyncio.run(_create_event_start_async(message))

    async def _create_event_start_async(message: Message):
        """Async реализация create_event_start."""
        logger.info(
            f"➕ Создание тренировки от @{message.from_user.username or message.from_user.id}"
        )

        user = await api_client.get_user_by_telegram_id(message.from_user.id)
        if not user:
            bot.send_message(message.chat.id, "❌ Пользователь не найден. Используйте /start")
            return

        if not user.get("age") or not user.get("city"):
            bot.send_message(
                message.chat.id,
                "⚠️ Сначала заполните профиль!\nИспользуйте /register для регистрации.",
                reply_markup=get_main_menu_keyboard(is_admin=bool(user.get("is_admin"))),
            )
            return

        bot.set_state(message.from_user.id, EventCreationStates.waiting_title, message.chat.id)
        bot.send_message(
            message.chat.id,
            "📝 Создание новой тренировки\n\n"
            "Введите название тренировки:\n\n"
            "💡 Используйте /cancel для отмены",
        )

    @bot.message_handler(state=EventCreationStates.waiting_title, content_types=["text"])
    @safe
    def process_event_title(message: Message):
        """Обработка названия события."""
        if message.text and message.text.startswith("/"):
            return
        if not message.text or len(message.text.strip()) < 3:
            bot.send_message(message.chat.id, "❌ Название должно быть не менее 3 символов")
            return

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["title"] = message.text.strip()

        bot.set_state(message.from_user.id, EventCreationStates.waiting_date, message.chat.id)
        bot.send_message(
            message.chat.id,
            "📅 Введите дату и время тренировки\n"
            "Формат: ДД.ММ.ГГГГ ЧЧ:ММ\n"
            "Например: 25.12.2024 18:00",
        )

    @bot.message_handler(state=EventCreationStates.waiting_date, content_types=["text"])
    @safe
    def process_event_date(message: Message):
        """Обработка даты события."""
        if message.text and message.text.startswith("/"):
            return
        if not message.text:
            bot.send_message(message.chat.id, "❌ Отправьте дату в формате ДД.ММ.ГГГГ ЧЧ:ММ")
            return

        try:
            date_obj = datetime.strptime(message.text.strip(), "%d.%m.%Y %H:%M")
            if date_obj < datetime.now():
                bot.send_message(message.chat.id, "❌ Дата не может быть в прошлом")
                return

            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data["date"] = date_obj.isoformat()

            bot.set_state(
                message.from_user.id, EventCreationStates.waiting_location, message.chat.id
            )
            bot.send_message(
                message.chat.id,
                "📍 Введите место проведения тренировки\n(или отправьте геолокацию)",
            )
        except ValueError:
            bot.send_message(
                message.chat.id,
                "❌ Неверный формат даты. Используйте: ДД.ММ.ГГГГ ЧЧ:ММ\nНапример: 25.12.2024 18:00",
            )

    @bot.message_handler(
        state=EventCreationStates.waiting_location,
        content_types=["text", "location"],
    )
    @safe
    def process_event_location(message: Message):
        """Обработка места проведения."""
        if message.text and message.text.startswith("/"):
            return
        location = latitude = longitude = None

        if message.location:
            latitude = message.location.latitude
            longitude = message.location.longitude
            location = f"📍 {latitude}, {longitude}"
        elif message.text:
            location = message.text.strip()

        if not location:
            bot.send_message(message.chat.id, "❌ Укажите место проведения")
            return

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data.update({"location": location, "latitude": latitude, "longitude": longitude})

        bot.set_state(message.from_user.id, EventCreationStates.waiting_sport_type, message.chat.id)
        bot.send_message(
            message.chat.id,
            "🏋️ Выберите вид спорта:",
            reply_markup=get_sport_keyboard("event_sport_"),
        )

    @bot.callback_query_handler(
        state=EventCreationStates.waiting_sport_type,
        func=lambda call: call.data.startswith("event_sport_"),
    )
    @safe_cb
    def process_event_sport_type(call):
        """Обработка выбора вида спорта."""
        sport_type = call.data.replace("event_sport_", "")

        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            data["sport_type"] = sport_type

        bot.answer_callback_query(call.id, f"✅ {sport_type}")
        bot.set_state(
            call.from_user.id, EventCreationStates.waiting_max_participants, call.message.chat.id
        )
        bot.send_message(
            call.message.chat.id,
            "👥 Сколько человек нужно?\n(отправьте число или '0' если без ограничений)",
        )

    @bot.message_handler(
        state=EventCreationStates.waiting_max_participants,
        content_types=["text"],
    )
    @safe
    def process_event_max_participants(message: Message):
        """Обработка количества участников."""
        if message.text and message.text.startswith("/"):
            return
        try:
            max_participants = int(message.text)
            max_participants = None if max_participants <= 0 else max_participants
        except (ValueError, AttributeError):
            bot.send_message(message.chat.id, "❌ Введите число или '0' если без ограничений")
            return

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["max_participants"] = max_participants

        bot.set_state(message.from_user.id, EventCreationStates.waiting_fee, message.chat.id)
        bot.send_message(
            message.chat.id, "💰 Есть ли взнос?\n(отправьте сумму в рублях или '0' если бесплатно)"
        )

    @bot.message_handler(state=EventCreationStates.waiting_fee, content_types=["text"])
    @safe
    def process_event_fee(message: Message):
        """Обработка взноса."""
        if message.text and message.text.startswith("/"):
            return
        try:
            fee = float(message.text.replace(",", "."))
            fee = None if fee <= 0 else fee
        except (ValueError, AttributeError):
            bot.send_message(message.chat.id, "❌ Введите сумму или '0' если бесплатно")
            return

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["fee"] = fee

        bot.set_state(message.from_user.id, EventCreationStates.waiting_note, message.chat.id)
        bot.send_message(
            message.chat.id, "📝 Добавьте примечание (опционально)\nИли отправьте 'пропустить'"
        )

    @bot.message_handler(state=EventCreationStates.waiting_note, content_types=["text"])
    @safe
    def process_event_note(message: Message):
        """Обработка примечания и создание события."""
        if message.text and message.text.startswith("/"):
            return
        asyncio.run(_process_event_note_async(message))

    async def _process_event_note_async(message: Message):
        """Async реализация process_event_note."""
        note = message.text.strip() if message.text.lower() != "пропустить" else None

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            user = await api_client.get_user_by_telegram_id(message.from_user.id)
            if not user:
                bot.send_message(message.chat.id, "❌ Пользователь не найден")
                bot.delete_state(message.from_user.id, message.chat.id)
                return

            event = await api_client.create_event(
                title=data["title"],
                date=data["date"],
                creator_id=user["id"],
                location=data.get("location"),
                latitude=data.get("latitude"),
                longitude=data.get("longitude"),
                sport_type=data.get("sport_type"),
                max_participants=data.get("max_participants"),
                fee=data.get("fee"),
                note=note,
            )

            bot.delete_state(message.from_user.id, message.chat.id)
            text = f"✅ Тренировка создана!\n\n{format_event_text(event)}"
            bot.send_message(
                message.chat.id,
                text,
                reply_markup=get_main_menu_keyboard(is_admin=bool(user.get("is_admin"))),
            )

    @bot.message_handler(func=lambda m: m.text == "🔍 Найти тренировку")
    @safe
    def search_events(message: Message):
        """Поиск тренировок."""
        asyncio.run(_search_events_async(message))

    async def _search_events_async(message: Message):
        """Async реализация search_events."""
        logger.info(f"🔍 Поиск тренировок от @{message.from_user.username or message.from_user.id}")

        user = await api_client.get_user_by_telegram_id(message.from_user.id)
        if not user:
            bot.send_message(message.chat.id, "❌ Пользователь не найден. Используйте /start")
            return

        events = await api_client.search_events(date_from=datetime.now().isoformat(), limit=20)

        # Исключаем собственные тренировки
        filtered_events = [e for e in events if e.get("creator_id") != user["id"]]

        if not filtered_events:
            bot.send_message(
                message.chat.id,
                "📭 Пока нет доступных тренировок.",
                reply_markup=get_main_menu_keyboard(is_admin=bool(user.get("is_admin"))),
            )
            return

        for event in filtered_events[:10]:
            keyboard = InlineKeyboardMarkup()
            keyboard.add(
                InlineKeyboardButton("📝 Подать заявку", callback_data=f"apply_{event['id']}")
            )
            bot.send_message(message.chat.id, format_event_text(event), reply_markup=keyboard)

        bot.send_message(
            message.chat.id,
            "Выберите действие:",
            reply_markup=get_main_menu_keyboard(is_admin=bool(user.get("is_admin"))),
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("apply_"))
    @safe_cb
    def apply_to_event(call):
        """Подать заявку на участие."""
        asyncio.run(_apply_to_event_async(call))

    async def _apply_to_event_async(call):
        """Async реализация apply_to_event."""
        event_id = int(call.data.replace("apply_", ""))

        applicant = await api_client.get_user_by_telegram_id(call.from_user.id)
        if not applicant:
            bot.answer_callback_query(call.id, "❌ Пользователь не найден")
            return

        application = await api_client.apply_to_event(event_id, applicant["id"])
        if not application:
            bot.answer_callback_query(call.id, "❌ Не удалось подать заявку")
            return

        bot.answer_callback_query(call.id, "✅ Заявка подана!")
        bot.send_message(
            call.message.chat.id,
            "📝 Ваша заявка отправлена создателю.\nВы получите уведомление после рассмотрения.",
        )

        # Уведомляем создателя
        event = await api_client.get_event(event_id)
        if event:
            creator = await api_client.get_user_by_id(event["creator_id"])
            if creator and creator.get("telegram_id"):
                notification = (
                    f"🔔 Новая заявка на вашу тренировку!\n\n"
                    f"{format_event_text(event)}\n"
                    f"От: {format_user_info(applicant)}\n\n"
                    f"Используйте /applications для просмотра"
                )
                try:
                    bot.send_message(creator["telegram_id"], notification)
                except Exception as e:
                    logger.error(f"Не удалось уведомить создателя: {e}")

    @bot.message_handler(func=lambda m: m.text == "📋 Мои тренировки")
    @safe
    def my_events(message: Message):
        """Показать тренировки пользователя."""
        asyncio.run(_my_events_async(message))

    async def _my_events_async(message: Message):
        """Async реализация my_events."""
        logger.info(f"📋 Мои тренировки от @{message.from_user.username or message.from_user.id}")

        user = await api_client.get_user_by_telegram_id(message.from_user.id)
        if not user:
            bot.send_message(message.chat.id, "❌ Пользователь не найден. Используйте /start")
            return

        created = await api_client.get_created_events(user["id"])
        participated = await api_client.get_user_events(user["id"])

        if not created and not participated:
            bot.send_message(
                message.chat.id,
                "📭 У вас пока нет тренировок.\nСоздайте свою или присоединитесь к существующей!",
                reply_markup=get_main_menu_keyboard(is_admin=bool(user.get("is_admin"))),
            )
            return

        text = "<b>📋 Ваши тренировки:</b>\n\n"
        if created:
            text += "<b>Созданные вами:</b>\n"
            for event in created[:5]:
                text += f"🏋️ {event['title']} - {event['date'][:16]}\n"
            text += "\n"
        if participated:
            text += "<b>Вы участвуете:</b>\n"
            for event in participated[:5]:
                text += f"🏋️ {event['title']} - {event['date'][:16]}\n"

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=get_main_menu_keyboard(is_admin=bool(user.get("is_admin"))),
        )
