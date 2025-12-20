"""
Обработчики регистрации и заполнения профиля.
"""

from loguru import logger
from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from api_client import api_client
from keyboards import get_main_menu_keyboard
from states import RegistrationStates
from utils import (
    create_callback_state_checker,
    create_state_checker,
    safe_callback,
    safe_handler,
)


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
        """Клавиатура выбора видов спорта."""
        sports = [
            "Футбол",
            "Баскетбол",
            "Волейбол",
            "Теннис",
            "Бег",
            "Йога",
            "Плавание",
            "Велоспорт",
            "Тренажёрный зал",
            "Бокс",
        ]
        keyboard = InlineKeyboardMarkup(row_width=2)
        for sport in sports:
            keyboard.add(InlineKeyboardButton(sport, callback_data=f"sport_{sport}"))
        keyboard.add(InlineKeyboardButton("✅ Готово", callback_data="sports_done"))
        return keyboard

    @bot.message_handler(commands=["register"])
    @safe
    def cmd_register(message: Message):
        """Начать регистрацию."""
        user = message.from_user
        logger.info(f"👤 /register от @{user.username} (id={user.id})")

        # Проверяем, есть ли уже пользователь
        api_user = api_client.get_user_by_telegram_id(user.id)
        if api_user and api_user.get("age") and api_user.get("city"):
            bot.send_message(
                message.chat.id,
                "✅ Вы уже зарегистрированы!\n" "Используйте /profile для редактирования данных.",
                reply_markup=get_main_menu_keyboard(),
            )
            return

        bot.set_state(message.from_user.id, RegistrationStates.waiting_age, message.chat.id)
        # Проверяем, что состояние установлено
        check_state = bot.get_state(message.from_user.id, message.chat.id)
        logger.info(
            f"✅ Состояние установлено: {check_state} (ожидалось: {RegistrationStates.waiting_age})"
        )
        bot.send_message(
            message.chat.id,
            "📝 Давайте заполним ваш профиль!\n\n"
            "Сколько вам лет? (отправьте число)\n\n"
            "💡 Используйте /cancel для отмены",
        )

    # Создаем функции проверки состояний
    check_waiting_age_state = create_state_checker(bot, RegistrationStates.waiting_age)
    check_waiting_city_state = create_state_checker(bot, RegistrationStates.waiting_city)
    check_gender_callback = create_callback_state_checker(
        bot, RegistrationStates.waiting_gender, "gender_"
    )
    check_sports_callback = create_callback_state_checker(
        bot,
        RegistrationStates.waiting_sports,
        "sport_",
        allowed_data=["sports_done"],  # Разрешаем "sports_done" без префикса
    )

    @bot.message_handler(func=check_waiting_age_state)
    @safe
    def process_age(message: Message):
        """Обработка возраста."""
        user = message.from_user

        logger.info(
            f"🎯 process_age вызван для @{user.username} (id={user.id}): text='{message.text}'"
        )
        logger.debug(f"Обработка возраста: text={message.text}, user_id={message.from_user.id}")

        if not message.text:
            logger.debug("Нет текста в сообщении")
            bot.send_message(message.chat.id, "❌ Пожалуйста, отправьте число (ваш возраст)")
            return

        try:
            # Пробуем преобразовать в число
            age = int(message.text.strip())
            logger.debug(f"Возраст распознан: {age}")

            if age < 10 or age > 100:
                bot.send_message(
                    message.chat.id,
                    "❌ Пожалуйста, введите реальный возраст (10-100)\n"
                    "Или используйте /cancel для отмены",
                )
                return

            # Сохраняем возраст
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data["age"] = age

            # Переходим к следующему шагу
            bot.set_state(message.from_user.id, RegistrationStates.waiting_gender, message.chat.id)
            bot.send_message(
                message.chat.id,
                "Выберите ваш пол:",
                reply_markup=get_gender_keyboard(),
            )
            logger.debug("Возраст успешно обработан, переходим к выбору пола")

        except (ValueError, TypeError) as e:
            # Не удалось преобразовать в число
            logger.debug(f"Ошибка преобразования возраста '{message.text}': {e}")
            bot.send_message(
                message.chat.id,
                "❌ Пожалуйста, введите число (ваш возраст)\n"
                "Например: 25\n\n"
                "Или используйте /cancel для отмены",
            )
        except Exception as e:
            # Неожиданная ошибка
            logger.error(f"Неожиданная ошибка при обработке возраста: {e}", exc_info=True)
            bot.send_message(
                message.chat.id,
                "❌ Произошла ошибка. Попробуйте ещё раз или используйте /cancel для отмены",
            )

    @bot.callback_query_handler(func=check_gender_callback)
    @safe_cb
    def process_gender(call):
        """Обработка выбора пола."""
        logger.info(
            f"🎯 process_gender вызван для @{call.from_user.username} (id={call.from_user.id}): data={call.data}"
        )

        gender_map = {"gender_male": "male", "gender_female": "female", "gender_other": "other"}
        gender = gender_map.get(call.data, "other")

        try:
            with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
                data["gender"] = gender

            bot.answer_callback_query(call.id, "✅ Пол сохранён")
            bot.set_state(call.from_user.id, RegistrationStates.waiting_city, call.message.chat.id)
            bot.send_message(
                call.message.chat.id,
                "В каком городе вы находитесь?\n" "Отправьте название города:",
            )
            logger.debug("Пол успешно обработан, переходим к выбору города")
        except Exception as e:
            logger.error(f"Ошибка при обработке выбора пола: {e}", exc_info=True)
            bot.answer_callback_query(call.id, "❌ Ошибка при сохранении")

    @bot.message_handler(func=check_waiting_city_state)
    @safe
    def process_city(message: Message):
        """Обработка города."""
        # Проверяем, что это не команда
        if message.text and message.text.startswith("/"):
            return  # Пропускаем команды

        if not message.text:
            bot.send_message(message.chat.id, "❌ Пожалуйста, отправьте название города")
            return

        try:
            city = message.text.strip()
            if len(city) < 2:
                bot.send_message(message.chat.id, "❌ Название города слишком короткое")
                return
        except Exception as e:
            logger.error(f"Ошибка при обработке города: {e}")
            bot.send_message(
                message.chat.id, "❌ Произошла ошибка. Попробуйте ещё раз или используйте /cancel"
            )
            return

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["city"] = city

        bot.set_state(message.from_user.id, RegistrationStates.waiting_sports, message.chat.id)
        bot.send_message(
            message.chat.id,
            "Выберите виды спорта, которыми вы занимаетесь:\n"
            "(можно выбрать несколько, затем нажмите 'Готово')",
            reply_markup=get_sports_keyboard(),
        )

    @bot.callback_query_handler(func=check_sports_callback)
    @safe_cb
    def process_sport_selection(call):
        """Обработка выбора видов спорта."""
        logger.info(
            f"🎯 process_sport_selection вызван для @{call.from_user.username} (id={call.from_user.id}): data={call.data}"
        )

        if call.data == "sports_done":
            with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
                sports = data.get("sports", [])

                if not sports:
                    bot.answer_callback_query(call.id, "❌ Выберите хотя бы один вид спорта")
                    return

                # Сохраняем данные в БД
                try:
                    api_user = api_client.get_user_by_telegram_id(call.from_user.id)
                    if api_user:
                        api_client.update_user(
                            api_user["id"],
                            age=data.get("age"),
                            gender=data.get("gender"),
                            city=data.get("city"),
                            sports=sports,
                        )
                    else:
                        # Создаём пользователя с полными данными
                        api_client.get_or_create_user(
                            telegram_id=call.from_user.id,
                            username=call.from_user.username,
                            first_name=call.from_user.first_name or "Пользователь",
                            age=data.get("age"),
                            gender=data.get("gender"),
                            city=data.get("city"),
                            sports=sports,
                        )

                    bot.delete_state(call.from_user.id, call.message.chat.id)

                    bot.answer_callback_query(call.id, "✅ Регистрация завершена!")
                    bot.send_message(
                        call.message.chat.id,
                        "🎉 Отлично! Ваш профиль создан.\n\n"
                        "Теперь вы можете:\n"
                        "• Создавать тренировки\n"
                        "• Искать и присоединяться к тренировкам\n"
                        "• Редактировать профиль",
                        reply_markup=get_main_menu_keyboard(),
                    )
                except Exception as e:
                    logger.error(f"Ошибка при сохранении профиля: {e}")
                    bot.answer_callback_query(call.id, "❌ Ошибка при сохранении")
        else:
            # Добавляем/удаляем вид спорта
            sport = call.data.replace("sport_", "")

            with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
                if "sports" not in data:
                    data["sports"] = []

                if sport in data["sports"]:
                    data["sports"].remove(sport)
                    bot.answer_callback_query(call.id, f"❌ {sport} удалён")
                else:
                    data["sports"].append(sport)
                    bot.answer_callback_query(call.id, f"✅ {sport} добавлен")

                selected = data["sports"]
                status = f"\n\nВыбрано: {', '.join(selected) if selected else 'ничего'}"
                bot.edit_message_text(
                    f"Выберите виды спорта:{status}",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=get_sports_keyboard(),
                )
