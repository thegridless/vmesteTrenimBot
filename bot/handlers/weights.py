"""
Обработчики для работы с весами пользователя.
"""

import asyncio
from datetime import date, datetime

from api_client import api_client
from common import get_main_menu_keyboard_for_user, get_user_or_error
from loguru import logger
from states import WeightStates
from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from utils import safe_callback, safe_handler


def register_weights_handlers(bot: TeleBot):
    """
    Регистрация обработчиков весов пользователя.

    Args:
        bot: Экземпляр TeleBot
    """
    safe = safe_handler(bot)
    safe_cb = safe_callback(bot)

    def get_weights_menu_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура меню весов."""
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("➕ Добавить вес", callback_data="weights_add"),
            InlineKeyboardButton("📈 Прогресс", callback_data="weights_progress"),
        )
        keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data="weights_back_main"))
        return keyboard

    def get_exercises_keyboard(
        exercises: list[str],
        prefix: str,
        include_new: bool = False,
        include_back: bool = True,
    ) -> InlineKeyboardMarkup:
        """
        Построить клавиатуру упражнений.

        Args:
            exercises: Список упражнений
            prefix: Префикс callback_data для индексов
            include_new: Добавить кнопку ручного ввода
            include_back: Добавить кнопку Назад
        """
        keyboard = InlineKeyboardMarkup(row_width=2)
        for idx, name in enumerate(exercises):
            keyboard.add(InlineKeyboardButton(name, callback_data=f"{prefix}{idx}"))
        if include_new:
            keyboard.add(InlineKeyboardButton("✍️ Ввести новое", callback_data="weight_ex_new"))
        if include_back:
            keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data="weights_menu"))
        return keyboard

    def format_weight_value(value: float) -> str:
        """
        Форматировать вес без лишних нулей.

        Args:
            value: Значение веса
        """
        text = f"{value:.2f}"
        return text.rstrip("0").rstrip(".")

    def format_date(value: str) -> str:
        """
        Привести дату в формат ДД.ММ.ГГГГ.

        Args:
            value: Дата в ISO формате
        """
        try:
            return datetime.fromisoformat(value).strftime("%d.%m.%Y")
        except ValueError:
            return value

    def get_date_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура выбора даты."""
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("📅 Сегодня", callback_data="weight_date_today"))
        return keyboard

    @bot.message_handler(func=lambda m: m.text == "⚖️ Мои рабочие веса")
    @safe
    def weights_menu(message: Message):
        """Показать меню весов."""
        bot.send_message(
            message.chat.id,
            "⚖️ <b>Мои рабочие веса</b>\nВыберите действие:",
            reply_markup=get_weights_menu_keyboard(),
        )

    @bot.callback_query_handler(func=lambda call: call.data == "weights_back_main")
    @safe_cb
    def weights_back_main(call):
        """Вернуться в главное меню."""
        bot.delete_state(call.from_user.id, call.message.chat.id)
        bot.answer_callback_query(call.id, "✅")
        keyboard = asyncio.run(get_main_menu_keyboard_for_user(api_client, call.from_user.id))
        bot.send_message(
            call.message.chat.id,
            "Выберите действие:",
            reply_markup=keyboard,
        )

    @bot.callback_query_handler(func=lambda call: call.data == "weights_menu")
    @safe_cb
    def weights_menu_callback(call):
        """Показать меню весов из callback."""
        bot.delete_state(call.from_user.id, call.message.chat.id)
        bot.answer_callback_query(call.id, "✅")
        bot.send_message(
            call.message.chat.id,
            "⚖️ <b>Мои рабочие веса</b>\nВыберите действие:",
            reply_markup=get_weights_menu_keyboard(),
        )

    @bot.callback_query_handler(func=lambda call: call.data == "weights_add")
    @safe_cb
    def start_add_weight(call):
        """Начать добавление веса."""
        asyncio.run(_start_add_weight_async(call))

    async def _start_add_weight_async(call):
        """Async реализация start_add_weight."""
        logger.info(
            f"⚖️ Добавление рабочего веса от @{call.from_user.username or call.from_user.id}"
        )
        user = await get_user_or_error(
            api_client,
            bot,
            call.from_user.id,
            call.message.chat.id,
        )
        if not user:
            return

        exercises = await api_client.get_weight_exercises(user["id"])

        bot.answer_callback_query(call.id, "✅")
        if exercises:
            bot.set_state(
                call.from_user.id, WeightStates.waiting_exercise_choice, call.message.chat.id
            )
        else:
            bot.set_state(
                call.from_user.id, WeightStates.waiting_exercise_input, call.message.chat.id
            )

        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            data["user_id"] = user["id"]
            data["exercises"] = exercises
        logger.debug(
            f"weights_add: user_id={user['id']} exercises={len(exercises)}",
        )

        if exercises:
            bot.send_message(
                call.message.chat.id,
                "Выберите упражнение или введите новое:",
                reply_markup=get_exercises_keyboard(exercises, "weight_ex_idx_", include_new=True),
            )
        else:
            bot.send_message(call.message.chat.id, "Введите название упражнения:")

    @bot.callback_query_handler(
        state=WeightStates.waiting_exercise_choice,
        func=lambda call: call.data == "weight_ex_new" or call.data.startswith("weight_ex_idx_"),
    )
    @safe_cb
    def process_exercise_choice(call):
        """Обработка выбора упражнения."""
        if call.data == "weight_ex_new":
            bot.set_state(
                call.from_user.id, WeightStates.waiting_exercise_input, call.message.chat.id
            )
            bot.answer_callback_query(call.id, "✅")
            bot.send_message(call.message.chat.id, "Введите название упражнения:")
            return

        idx_str = call.data.replace("weight_ex_idx_", "")
        try:
            idx = int(idx_str)
        except ValueError:
            bot.answer_callback_query(call.id, "❌ Ошибка выбора")
            return

        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            exercises = data.get("exercises", [])
            if idx < 0 or idx >= len(exercises):
                bot.answer_callback_query(call.id, "❌ Упражнение не найдено")
                return
            data["exercise"] = exercises[idx]
        logger.debug(f"weights_add: выбранное упражнение={exercises[idx]}")

        bot.answer_callback_query(call.id, "✅")
        bot.set_state(call.from_user.id, WeightStates.waiting_date, call.message.chat.id)
        bot.send_message(
            call.message.chat.id,
            "Введите дату замера (ДД.ММ.ГГГГ):",
            reply_markup=get_date_keyboard(),
        )

    @bot.message_handler(state=WeightStates.waiting_exercise_input, content_types=["text"])
    @safe
    def process_exercise_input(message: Message):
        """Обработка ручного ввода упражнения."""
        if message.text and message.text.startswith("/"):
            return
        if not message.text or len(message.text.strip()) < 2:
            bot.send_message(message.chat.id, "❌ Введите корректное название упражнения")
            return

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["exercise"] = message.text.strip()
        logger.debug(f"weights_add: введённое упражнение={message.text.strip()}")

        bot.set_state(message.from_user.id, WeightStates.waiting_date, message.chat.id)
        bot.send_message(
            message.chat.id,
            "Введите дату замера (ДД.ММ.ГГГГ):",
            reply_markup=get_date_keyboard(),
        )

    @bot.callback_query_handler(
        state=WeightStates.waiting_date,
        func=lambda call: call.data == "weight_date_today",
    )
    @safe_cb
    def process_weight_date_today(call):
        """Выбор текущей даты замера."""
        today_value = date.today().isoformat()
        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            data["date"] = today_value
        logger.debug(f"weights_add: дата={today_value}")

        bot.answer_callback_query(call.id, "✅")
        bot.set_state(call.from_user.id, WeightStates.waiting_weight, call.message.chat.id)
        bot.send_message(call.message.chat.id, "Введите вес (например, 45.5):")

    @bot.message_handler(state=WeightStates.waiting_date, content_types=["text"])
    @safe
    def process_weight_date(message: Message):
        """Обработка даты замера."""
        if message.text and message.text.startswith("/"):
            return
        if not message.text:
            bot.send_message(message.chat.id, "❌ Укажите дату в формате ДД.ММ.ГГГГ")
            return

        try:
            date_obj = datetime.strptime(message.text.strip(), "%d.%m.%Y").date()
            if date_obj > date.today():
                bot.send_message(message.chat.id, "❌ Дата не может быть в будущем")
                return
        except ValueError:
            bot.send_message(message.chat.id, "❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ")
            return

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["date"] = date_obj.isoformat()
        logger.debug(f"weights_add: дата={data['date']}")

        bot.set_state(message.from_user.id, WeightStates.waiting_weight, message.chat.id)
        bot.send_message(message.chat.id, "Введите вес (например, 45.5):")

    @bot.message_handler(state=WeightStates.waiting_weight, content_types=["text"])
    @safe
    def process_weight_value(message: Message):
        """Обработка веса и сохранение записи."""
        if message.text and message.text.startswith("/"):
            return
        try:
            weight_value = float(message.text.replace(",", "."))
            if weight_value <= 0:
                raise ValueError
        except (ValueError, AttributeError):
            bot.send_message(message.chat.id, "❌ Введите корректный вес (например, 45.5)")
            return

        asyncio.run(_save_weight_async(message, weight_value))

    async def _save_weight_async(message: Message, weight_value: float):
        """Async сохранение записи веса."""
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            user_id = data.get("user_id")
            exercise = data.get("exercise")
            date_value = data.get("date")

        logger.debug(
            f"weights_add: сохранение user_id={user_id} exercise={exercise} date={date_value} weight={weight_value}",
        )
        if not user_id or not exercise or not date_value:
            bot.send_message(message.chat.id, "❌ Не удалось сохранить запись. Попробуйте ещё раз.")
            return

        await api_client.create_weight(
            user_id=user_id,
            exercise=exercise,
            date=date_value,
            weight=weight_value,
        )

        bot.delete_state(message.from_user.id, message.chat.id)
        keyboard = await get_main_menu_keyboard_for_user(api_client, message.from_user.id)
        bot.send_message(
            message.chat.id,
            f"✅ Запись добавлена: {exercise} — {format_weight_value(weight_value)} кг",
            reply_markup=keyboard,
        )

    @bot.callback_query_handler(func=lambda call: call.data == "weights_progress")
    @safe_cb
    def start_progress(call):
        """Начать просмотр прогресса."""
        asyncio.run(_start_progress_async(call))

    async def _start_progress_async(call):
        """Async реализация start_progress."""
        logger.info(f"📈 Прогресс весов от @{call.from_user.username or call.from_user.id}")
        user = await get_user_or_error(
            api_client,
            bot,
            call.from_user.id,
            call.message.chat.id,
        )
        if not user:
            return

        exercises = await api_client.get_weight_exercises(user["id"])
        if not exercises:
            bot.answer_callback_query(call.id, "ℹ️")
            bot.send_message(
                call.message.chat.id,
                "У вас пока нет упражнений. Добавьте первую запись веса.",
                reply_markup=get_weights_menu_keyboard(),
            )
            return

        bot.answer_callback_query(call.id, "✅")
        bot.set_state(
            call.from_user.id, WeightStates.waiting_progress_exercise, call.message.chat.id
        )

        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            data["user_id"] = user["id"]
            data["exercises"] = exercises
        bot.send_message(
            call.message.chat.id,
            "Выберите упражнение для просмотра прогресса:",
            reply_markup=get_exercises_keyboard(exercises, "weight_prog_idx_", include_back=True),
        )

    @bot.callback_query_handler(
        state=WeightStates.waiting_progress_exercise,
        func=lambda call: call.data.startswith("weight_prog_idx_"),
    )
    @safe_cb
    def process_progress_exercise(call):
        """Обработка выбора упражнения для прогресса."""
        asyncio.run(_process_progress_exercise_async(call))

    async def _process_progress_exercise_async(call):
        """Async реализация process_progress_exercise."""
        idx_str = call.data.replace("weight_prog_idx_", "")
        try:
            idx = int(idx_str)
        except ValueError:
            bot.answer_callback_query(call.id, "❌ Ошибка выбора")
            return

        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            user_id = data.get("user_id")
            exercises = data.get("exercises", [])

        if not user_id or idx < 0 or idx >= len(exercises):
            bot.answer_callback_query(call.id, "❌ Упражнение не найдено")
            return

        exercise = exercises[idx]
        items = await api_client.get_weight_progress(user_id, exercise, limit=5)
        if not items:
            bot.answer_callback_query(call.id, "ℹ️")
            bot.send_message(call.message.chat.id, "Нет данных по этому упражнению.")
            return

        ordered = list(reversed(items))
        first_weight = ordered[0]["weight"]
        last_weight = ordered[-1]["weight"]
        delta = last_weight - first_weight if len(ordered) > 1 else 0
        if delta > 0:
            delta_text = f"⬆️ +{format_weight_value(delta)} кг"
        elif delta < 0:
            delta_text = f"⬇️ {format_weight_value(delta)} кг"
        else:
            delta_text = "— без изменений"

        text = f"📈 <b>{exercise}</b>\n"
        for item in ordered:
            text += f"• {format_date(item['date'])}: {format_weight_value(item['weight'])} кг\n"
        if len(ordered) > 1:
            text += f"\nΔ {delta_text}"

        bot.answer_callback_query(call.id, "✅")
        bot.delete_state(call.from_user.id, call.message.chat.id)
        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=get_weights_menu_keyboard(),
        )
