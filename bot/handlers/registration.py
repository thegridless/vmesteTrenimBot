"""
Обработчики регистрации и заполнения профиля.
"""

import asyncio

from api_client import api_client
from common import get_sport_keyboard
from keyboards import get_main_menu_keyboard
from loguru import logger
from states import RegistrationStates
from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from utils import safe_callback, safe_handler


def register_registration_handlers(bot: TeleBot):
    """
    Регистрация обработчиков регистрации.

    Args:
        bot: Экземпляр TeleBot
    """
    # Создаём декораторы для безопасной обработки ошибок
    safe = safe_handler(bot)
    safe_cb = safe_callback(bot)

    def get_gender_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура выбора пола."""
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("Мужской", callback_data="gender_male"))
        keyboard.add(InlineKeyboardButton("Женский", callback_data="gender_female"))
        return keyboard

    def get_sports_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура выбора видов спорта с кнопкой Готово."""
        keyboard = get_sport_keyboard()
        keyboard.add(InlineKeyboardButton("✅ Готово", callback_data="sports_done"))
        return keyboard

    @bot.message_handler(commands=["register"])
    @safe
    def cmd_register(message: Message):
        """Начать регистрацию."""
        asyncio.run(_cmd_register_async(message))

    async def _cmd_register_async(message: Message):
        """Async реализация cmd_register."""
        logger.info(f"📝 Регистрация от @{message.from_user.username or message.from_user.id}")

        api_user = await api_client.get_user_by_telegram_id(message.from_user.id)
        if api_user and api_user.get("age") and api_user.get("city"):
            bot.send_message(
                message.chat.id,
                "✅ Вы уже зарегистрированы!\nИспользуйте /profile для просмотра.",
                reply_markup=get_main_menu_keyboard(is_admin=bool(api_user.get("is_admin"))),
            )
            return

        bot.set_state(message.from_user.id, RegistrationStates.waiting_age, message.chat.id)
        bot.send_message(
            message.chat.id,
            "📝 Давайте заполним ваш профиль!\n\n"
            "Сколько вам лет? (отправьте число)\n\n"
            "💡 Используйте /cancel для отмены",
        )

    @bot.message_handler(state=RegistrationStates.waiting_age, content_types=["text"])
    @safe
    def process_age(message: Message):
        """Обработка возраста."""
        if message.text and message.text.startswith("/"):
            return
        try:
            age = int(message.text.strip())
            if not (10 <= age <= 100):
                bot.send_message(message.chat.id, "❌ Введите возраст от 10 до 100 лет")
                return
        except (ValueError, AttributeError):
            bot.send_message(message.chat.id, "❌ Введите число (ваш возраст)")
            return

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["age"] = age

        bot.set_state(message.from_user.id, RegistrationStates.waiting_gender, message.chat.id)
        bot.send_message(message.chat.id, "Выберите ваш пол:", reply_markup=get_gender_keyboard())

    @bot.callback_query_handler(
        state=RegistrationStates.waiting_gender,
        func=lambda call: call.data.startswith("gender_"),
    )
    @safe_cb
    def process_gender(call):
        """Обработка выбора пола."""
        gender = "male" if call.data == "gender_male" else "female"

        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            data["gender"] = gender

        bot.answer_callback_query(call.id, "✅")
        bot.set_state(call.from_user.id, RegistrationStates.waiting_city, call.message.chat.id)
        bot.send_message(
            call.message.chat.id, "В каком городе вы находитесь?\nОтправьте название города:"
        )

    @bot.message_handler(state=RegistrationStates.waiting_city, content_types=["text"])
    @safe
    def process_city(message: Message):
        """Обработка города."""
        if message.text and message.text.startswith("/"):
            return
        if not message.text or len(message.text.strip()) < 2:
            bot.send_message(message.chat.id, "❌ Введите корректное название города")
            return

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["city"] = message.text.strip()

        bot.set_state(message.from_user.id, RegistrationStates.waiting_sports, message.chat.id)
        bot.send_message(
            message.chat.id,
            "Выберите виды спорта:\n(можно выбрать несколько, затем нажмите 'Готово')",
            reply_markup=get_sports_keyboard(),
        )

    @bot.callback_query_handler(
        state=RegistrationStates.waiting_sports,
        func=lambda call: call.data.startswith("sport_") or call.data == "sports_done",
    )
    @safe_cb
    def process_sport_selection(call):
        """Обработка выбора видов спорта."""
        asyncio.run(_process_sport_selection_async(call))

    async def _process_sport_selection_async(call):
        """Async реализация process_sport_selection."""
        if call.data == "sports_done":
            with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
                sports = data.get("sports", [])
                if not sports:
                    bot.answer_callback_query(call.id, "❌ Выберите хотя бы один вид спорта")
                    return

                api_user = await api_client.get_user_by_telegram_id(call.from_user.id)
                if api_user:
                    await api_client.update_user(
                        api_user["id"],
                        age=data.get("age"),
                        gender=data.get("gender"),
                        city=data.get("city"),
                        sports=sports,
                    )
                else:
                    await api_client.get_or_create_user(
                        telegram_id=call.from_user.id,
                        username=call.from_user.username,
                        first_name=call.from_user.first_name or "Пользователь",
                        age=data.get("age"),
                        gender=data.get("gender"),
                        city=data.get("city"),
                        sports=sports,
                    )

                bot.delete_state(call.from_user.id, call.message.chat.id)
                bot.answer_callback_query(call.id, "✅ Готово!")
                updated_user = await api_client.get_user_by_telegram_id(call.from_user.id)
                bot.send_message(
                    call.message.chat.id,
                    "🎉 Профиль создан!\n\nТеперь вы можете:\n• Создавать тренировки\n• Искать тренировки\n• Редактировать профиль",
                    reply_markup=get_main_menu_keyboard(
                        is_admin=bool(updated_user and updated_user.get("is_admin"))
                    ),
                )
        else:
            sport = call.data.replace("sport_", "")
            with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
                if "sports" not in data:
                    data["sports"] = []

                if sport in data["sports"]:
                    data["sports"].remove(sport)
                    bot.answer_callback_query(call.id, f"❌ {sport}")
                else:
                    data["sports"].append(sport)
                    bot.answer_callback_query(call.id, f"✅ {sport}")

                selected = data["sports"]
                status = f"\n\nВыбрано: {', '.join(selected) if selected else 'ничего'}"
                bot.edit_message_text(
                    f"Выберите виды спорта:{status}",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=get_sports_keyboard(),
                )
