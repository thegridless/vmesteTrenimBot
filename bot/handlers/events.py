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
from utils import (
    check_state,
    create_callback_state_checker,
    create_state_checker,
    safe_callback,
    safe_handler,
)


def register_events_handlers(bot: TeleBot):
    """
    Регистрация обработчиков событий.

    Args:
        bot: Экземпляр TeleBot
    """
    # Создаём декораторы для безопасной обработки ошибок
    safe = safe_handler(bot)
    safe_cb = safe_callback(bot)

    # Создаем функции проверки состояний
    check_waiting_title = create_state_checker(bot, EventCreationStates.waiting_title)
    check_waiting_date = create_state_checker(bot, EventCreationStates.waiting_date)
    check_waiting_location = create_state_checker(bot, EventCreationStates.waiting_location)
    check_waiting_max_participants = create_state_checker(
        bot, EventCreationStates.waiting_max_participants
    )
    check_waiting_fee = create_state_checker(bot, EventCreationStates.waiting_fee)
    check_waiting_note = create_state_checker(bot, EventCreationStates.waiting_note)
    check_event_sport_callback = create_callback_state_checker(
        bot, EventCreationStates.waiting_sport_type, "event_sport_"
    )

    @bot.message_handler(func=lambda m: m.text == "➕ Создать тренировку")
    @safe
    def create_event_start(message: Message):
        """Начать создание события."""
        asyncio.run(_create_event_start_async(message))

    async def _create_event_start_async(message: Message):
        """Async реализация create_event_start."""
        logger.info(f"➕ Создание тренировки от @{message.from_user.username or message.from_user.id}")

        user = await api_client.get_user_by_telegram_id(message.from_user.id)
        if not user:
            bot.send_message(message.chat.id, "❌ Пользователь не найден. Используйте /start")
            return

        if not user.get("age") or not user.get("city"):
            bot.send_message(
                message.chat.id,
                "⚠️ Сначала заполните профиль!\nИспользуйте /register для регистрации.",
                reply_markup=get_main_menu_keyboard(),
            )
            return

        bot.set_state(message.from_user.id, EventCreationStates.waiting_title, message.chat.id)
        bot.send_message(
            message.chat.id,
            "📝 Создание новой тренировки\n\n"
            "Введите название тренировки:\n\n"
            "💡 Используйте /cancel для отмены",
        )

    @bot.message_handler(func=check_waiting_title)
    @safe
    def process_event_title(message: Message):
        """Обработка названия события."""
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

    @bot.message_handler(func=check_waiting_date)
    @safe
    def process_event_date(message: Message):
        """Обработка даты события."""
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

            bot.set_state(message.from_user.id, EventCreationStates.waiting_location, message.chat.id)
            bot.send_message(message.chat.id, "📍 Введите место проведения тренировки\n(или отправьте геолокацию)")
        except ValueError:
            bot.send_message(
                message.chat.id,
                "❌ Неверный формат даты. Используйте: ДД.ММ.ГГГГ ЧЧ:ММ\nНапример: 25.12.2024 18:00",
            )

    def check_waiting_location_with_types(message: Message) -> bool:
        """Проверка состояния waiting_location с поддержкой text и location."""
        if message.text and message.text.startswith("/"):
            return False
        if message.content_type not in ["text", "location"]:
            return False
        return check_state(
            bot,
            message.from_user.id,
            message.chat.id,
            EventCreationStates.waiting_location,
            skip_commands=False,
        )

    @bot.message_handler(func=check_waiting_location_with_types)
    @safe
    def process_event_location(message: Message):
        """Обработка места проведения."""
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
        bot.send_message(message.chat.id, "🏋️ Выберите вид спорта:", reply_markup=get_sport_keyboard("event_sport_"))

    @bot.callback_query_handler(func=check_event_sport_callback)
    @safe_cb
    def process_event_sport_type(call):
        """Обработка выбора вида спорта."""
        sport_type = call.data.replace("event_sport_", "")

        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            data["sport_type"] = sport_type

        bot.answer_callback_query(call.id, f"✅ {sport_type}")
        bot.set_state(call.from_user.id, EventCreationStates.waiting_max_participants, call.message.chat.id)
        bot.send_message(
            call.message.chat.id,
            "👥 Сколько человек нужно?\n(отправьте число или '0' если без ограничений)",
        )

    @bot.message_handler(func=check_waiting_max_participants)
    @safe
    def process_event_max_participants(message: Message):
        """Обработка количества участников."""
        try:
            max_participants = int(message.text)
            max_participants = None if max_participants <= 0 else max_participants
        except (ValueError, AttributeError):
            bot.send_message(message.chat.id, "❌ Введите число или '0' если без ограничений")
            return

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["max_participants"] = max_participants

        bot.set_state(message.from_user.id, EventCreationStates.waiting_fee, message.chat.id)
        bot.send_message(message.chat.id, "💰 Есть ли взнос?\n(отправьте сумму в рублях или '0' если бесплатно)")

    @bot.message_handler(func=check_waiting_fee)
    @safe
    def process_event_fee(message: Message):
        """Обработка взноса."""
        try:
            fee = float(message.text.replace(",", "."))
            fee = None if fee <= 0 else fee
        except (ValueError, AttributeError):
            bot.send_message(message.chat.id, "❌ Введите сумму или '0' если бесплатно")
            return

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["fee"] = fee

        bot.set_state(message.from_user.id, EventCreationStates.waiting_note, message.chat.id)
        bot.send_message(message.chat.id, "📝 Добавьте примечание (опционально)\nИли отправьте 'пропустить'")

    @bot.message_handler(func=check_waiting_note)
    @safe
    def process_event_note(message: Message):
        """Обработка примечания и создание события."""
        logger.info(
            f"🎯 process_event_note вызван для @{message.from_user.username} (id={message.from_user.id}): text='{message.text}'"
        )

        if not message.text:
            bot.send_message(
                message.chat.id, "❌ Пожалуйста, отправьте примечание или 'пропустить'"
            )
            return

        try:
            note = message.text.strip() if message.text.lower() != "пропустить" else None
        except Exception as e:
            logger.error(f"Ошибка при обработке примечания: {e}")
            bot.send_message(
                message.chat.id, "❌ Произошла ошибка. Попробуйте ещё раз или используйте /cancel"
            )
            return

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            user = api_client.get_user_by_telegram_id(message.from_user.id)
            if not user:
                bot.send_message(message.chat.id, "❌ Пользователь не найден")
                bot.delete_state(message.from_user.id, message.chat.id)
                return

            try:
                event = api_client.create_event(
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

                text = "✅ Тренировка создана!\n\n"
                text += f"🏋️ <b>{event['title']}</b>\n"
                text += f"📅 {event['date']}\n"
                if event.get("location"):
                    text += f"📍 {event['location']}\n"
                if event.get("sport_type"):
                    text += f"⚽ {event['sport_type']}\n"
                if event.get("max_participants"):
                    text += f"👥 До {event['max_participants']} человек\n"
                if event.get("fee"):
                    text += f"💰 Взнос: {event['fee']} руб.\n"

                bot.send_message(message.chat.id, text, reply_markup=get_main_menu_keyboard())
            except Exception as e:
                logger.error(f"Ошибка при создании события: {e}")
                bot.send_message(
                    message.chat.id,
                    "❌ Ошибка при создании тренировки. Попробуйте позже.",
                    reply_markup=get_main_menu_keyboard(),
                )

    @bot.message_handler(func=lambda m: m.text == "🔍 Найти тренировку")
    @safe
    def search_events(message: Message):
        """Поиск тренировок."""
        user_tg = message.from_user
        logger.info(f"👤 Команда 'Найти тренировку' от @{user_tg.username} (id={user_tg.id})")

        user = api_client.get_user_by_telegram_id(user_tg.id)
        if not user:
            bot.send_message(message.chat.id, "❌ Пользователь не найден. Используйте /start")
            return

        try:
            # Получаем все активные события (дата в будущем)
            from datetime import datetime

            events = api_client.search_events(
                date_from=datetime.now().isoformat(),
                limit=20,
            )

            if not events:
                bot.send_message(
                    message.chat.id,
                    "📭 Пока нет доступных тренировок.",
                    reply_markup=get_main_menu_keyboard(),
                )
                return

            # Фильтруем события: исключаем тренировки, созданные пользователем
            filtered_events = [event for event in events if event.get("creator_id") != user["id"]]

            if not filtered_events:
                bot.send_message(
                    message.chat.id,
                    "📭 Пока нет доступных тренировок от других пользователей.",
                    reply_markup=get_main_menu_keyboard(),
                )
                return

            # Отправляем каждое событие отдельным сообщением с кнопкой
            for event in filtered_events[:10]:
                text = f"🏋️ <b>{event['title']}</b>\n"
                text += f"📅 {event['date'][:16]}\n"
                if event.get("location"):
                    text += f"📍 {event['location']}\n"
                if event.get("sport_type"):
                    text += f"⚽ {event['sport_type']}\n"
                if event.get("max_participants"):
                    text += f"👥 До {event['max_participants']} чел.\n"
                if event.get("fee"):
                    text += f"💰 {event['fee']} руб.\n"

                # Кнопка для подачи заявки
                keyboard = InlineKeyboardMarkup()
                keyboard.add(
                    InlineKeyboardButton(
                        "📝 Подать заявку",
                        callback_data=f"apply_{event['id']}",
                    )
                )
                bot.send_message(message.chat.id, text, reply_markup=keyboard)

            bot.send_message(
                message.chat.id,
                "Выберите действие:",
                reply_markup=get_main_menu_keyboard(),
            )
        except Exception as e:
            logger.error(f"Ошибка при поиске тренировок: {e}")
            bot.send_message(message.chat.id, "❌ Ошибка при загрузке тренировок.")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("apply_"))
    @safe_cb
    def apply_to_event(call):
        """Подать заявку на участие."""
        event_id = int(call.data.replace("apply_", ""))
        applicant_user = api_client.get_user_by_telegram_id(call.from_user.id)

        if not applicant_user:
            bot.answer_callback_query(call.id, "❌ Пользователь не найден")
            return

        try:
            application = api_client.apply_to_event(event_id, applicant_user["id"])
            if application:
                bot.answer_callback_query(call.id, "✅ Заявка подана!")
                bot.send_message(
                    call.message.chat.id,
                    "📝 Ваша заявка на участие отправлена создателю.\n"
                    "Вы получите уведомление после рассмотрения.",
                )

                # Уведомляем создателя о новой заявке
                try:
                    event = api_client.get_event(event_id)
                    if event:
                        creator = api_client.get_user_by_id(event["creator_id"])
                        if creator and creator.get("telegram_id"):
                            notification = (
                                f"🔔 Новая заявка на вашу тренировку!\n\n"
                                f"🏋️ <b>{event['title']}</b>\n"
                                f"👤 От: {applicant_user['first_name']}"
                            )
                            if applicant_user.get("age"):
                                notification += f", {applicant_user['age']} лет"
                            notification += "\n\nИспользуйте /applications для просмотра заявок"

                            bot.send_message(creator["telegram_id"], notification)
                except Exception as e:
                    logger.error(f"Ошибка при отправке уведомления создателю: {e}")
            else:
                bot.answer_callback_query(call.id, "❌ Не удалось подать заявку")
        except Exception as e:
            logger.error(f"Ошибка при подаче заявки: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка")

    @bot.message_handler(func=lambda m: m.text == "📋 Мои тренировки")
    @safe
    def my_events(message: Message):
        """Показать тренировки пользователя."""
        user_tg = message.from_user
        logger.info(f"👤 Команда 'Мои тренировки' от @{user_tg.username} (id={user_tg.id})")

        user = api_client.get_user_by_telegram_id(user_tg.id)
        if not user:
            bot.send_message(message.chat.id, "❌ Пользователь не найден. Используйте /start")
            return

        try:
            # Созданные события
            created = api_client.get_created_events(user["id"])
            # События где пользователь участник
            participated = api_client.get_user_events(user["id"])

            if not created and not participated:
                bot.send_message(
                    message.chat.id,
                    "📭 У вас пока нет тренировок.\n"
                    "Создайте свою или присоединитесь к существующей!",
                    reply_markup=get_main_menu_keyboard(),
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

            bot.send_message(message.chat.id, text, reply_markup=get_main_menu_keyboard())
        except Exception as e:
            logger.error(f"Ошибка при загрузке тренировок: {e}")
            bot.send_message(message.chat.id, "❌ Ошибка при загрузке тренировок.")
