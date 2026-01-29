"""
Обработчики администрирования.
"""

import asyncio

from api_client import api_client
from common import get_admin_or_error
from keyboards import get_admin_menu_keyboard, get_main_menu_keyboard
from loguru import logger
from states import AdminStates
from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from utils import safe_callback, safe_handler


def register_admin_handlers(bot: TeleBot):
    """
    Регистрация обработчиков администрирования.

    Args:
        bot: Экземпляр TeleBot
    """
    safe = safe_handler(bot)
    safe_cb = safe_callback(bot)

    def format_user_label(user: dict) -> str:
        """
        Сформировать подпись пользователя для списка.

        Args:
            user: Данные пользователя

        Returns:
            Подпись для кнопки
        """
        name = user.get("first_name") or "Пользователь"
        username = user.get("username")
        if username:
            return f"{name} (@{username})"
        return name

    async def send_user_page(message: Message, page: int) -> None:
        """
        Отправить страницу выбора пользователя.

        Args:
            message: Сообщение админа
            page: Номер страницы (с 0)
        """
        admin_user = await get_admin_or_error(
            api_client,
            bot,
            message.from_user.id,
            message.chat.id,
        )
        if not admin_user:
            return

        limit = 10
        skip = page * limit
        users = await api_client.get_admin_users(admin_user["telegram_id"], skip=skip, limit=limit)

        keyboard = InlineKeyboardMarkup(row_width=1)
        for user in users:
            telegram_id = user.get("telegram_id")
            if not telegram_id:
                continue
            label = format_user_label(user)
            keyboard.add(
                InlineKeyboardButton(
                    label,
                    callback_data=f"adm_user_{user['id']}_{telegram_id}",
                )
            )

        nav = InlineKeyboardMarkup(row_width=2)
        if page > 0:
            nav.add(InlineKeyboardButton("⬅️ Назад", callback_data=f"adm_user_page_{page - 1}"))
        if len(users) == limit:
            nav.add(InlineKeyboardButton("➡️ Вперёд", callback_data=f"adm_user_page_{page + 1}"))

        if nav.keyboard:
            for row in nav.keyboard:
                keyboard.keyboard.append(row)

        keyboard.add(InlineKeyboardButton("❌ Отмена", callback_data="adm_user_cancel"))

        bot.send_message(
            message.chat.id,
            "Выберите пользователя для личного сообщения:",
            reply_markup=keyboard,
        )

    @bot.message_handler(func=lambda m: m.text == "Администрирование")
    @safe
    def admin_menu(message: Message):
        """Показать админ-меню."""
        asyncio.run(_admin_menu_async(message))

    async def _admin_menu_async(message: Message):
        """Async реализация admin_menu."""
        admin_user = await get_admin_or_error(
            api_client,
            bot,
            message.from_user.id,
            message.chat.id,
        )
        if not admin_user:
            return
        bot.send_message(
            message.chat.id,
            "🛠 Администрирование\nВыберите действие:",
            reply_markup=get_admin_menu_keyboard(),
        )

    @bot.message_handler(func=lambda m: m.text == "⬅️ Назад")
    @safe
    def admin_back(message: Message):
        """Вернуться в главное меню из админ-меню."""
        asyncio.run(_admin_back_async(message))

    async def _admin_back_async(message: Message):
        """Async реализация admin_back."""
        admin_user = await get_admin_or_error(
            api_client,
            bot,
            message.from_user.id,
            message.chat.id,
        )
        if not admin_user:
            return
        bot.send_message(
            message.chat.id,
            "Выберите действие:",
            reply_markup=get_main_menu_keyboard(is_admin=True),
        )

    @bot.message_handler(func=lambda m: m.text == "📣 Рассылка всем")
    @safe
    def start_broadcast(message: Message):
        """Начать создание рассылки."""
        asyncio.run(_start_broadcast_async(message))

    async def _start_broadcast_async(message: Message):
        """Async реализация start_broadcast."""
        admin_user = await get_admin_or_error(
            api_client,
            bot,
            message.from_user.id,
            message.chat.id,
        )
        if not admin_user:
            return
        bot.set_state(message.from_user.id, AdminStates.waiting_broadcast_text, message.chat.id)
        bot.send_message(
            message.chat.id,
            "Введите текст рассылки:\n\n💡 Используйте /cancel для отмены",
            reply_markup=get_admin_menu_keyboard(),
        )

    @bot.message_handler(func=lambda m: m.text == "✉️ Личное сообщение")
    @safe
    def start_personal_message(message: Message):
        """Начать отправку личного сообщения."""
        asyncio.run(_start_personal_message_async(message))

    async def _start_personal_message_async(message: Message):
        """Async реализация start_personal_message."""
        admin_user = await get_admin_or_error(
            api_client,
            bot,
            message.from_user.id,
            message.chat.id,
        )
        if not admin_user:
            return

        bot.set_state(message.from_user.id, AdminStates.waiting_personal_select, message.chat.id)
        await send_user_page(message, page=0)

    @bot.callback_query_handler(
        state=AdminStates.waiting_personal_select,
        func=lambda call: call.data.startswith("adm_user_")
        or call.data.startswith("adm_user_page_")
        or call.data == "adm_user_cancel",
    )
    @safe_cb
    def process_personal_user_select(call):
        """Выбор пользователя для личного сообщения."""
        if call.data == "adm_user_cancel":
            bot.delete_state(call.from_user.id, call.message.chat.id)
            bot.answer_callback_query(call.id, "❌ Отменено")
            bot.send_message(
                call.message.chat.id,
                "Действие отменено.",
                reply_markup=get_admin_menu_keyboard(),
            )
            return

        if call.data.startswith("adm_user_page_"):
            page = int(call.data.replace("adm_user_page_", ""))
            bot.answer_callback_query(call.id, "✅")
            asyncio.run(send_user_page(call.message, page=page))
            return

        _, _, user_id_str, telegram_id_str = call.data.split("_", 3)
        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            data["target_user_id"] = int(user_id_str)
            data["target_telegram_id"] = int(telegram_id_str)

        bot.answer_callback_query(call.id, "✅")
        bot.set_state(call.from_user.id, AdminStates.waiting_personal_text, call.message.chat.id)
        bot.send_message(
            call.message.chat.id,
            "Введите текст личного сообщения:",
            reply_markup=get_admin_menu_keyboard(),
        )

    @bot.message_handler(state=AdminStates.waiting_personal_text, content_types=["text"])
    @safe
    def process_personal_text(message: Message):
        """Обработка текста личного сообщения."""
        if message.text and message.text.startswith("/"):
            return
        text = (message.text or "").strip()
        if not text:
            bot.send_message(message.chat.id, "❌ Введите текст сообщения")
            return

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["personal_text"] = text

        bot.set_state(message.from_user.id, AdminStates.waiting_personal_confirm, message.chat.id)
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("✅ Отправить", callback_data="personal_send"),
            InlineKeyboardButton("❌ Отмена", callback_data="personal_cancel"),
        )
        bot.send_message(
            message.chat.id,
            f"✉️ <b>Предпросмотр сообщения</b>\n\n{text}",
            reply_markup=keyboard,
        )

    @bot.callback_query_handler(
        state=AdminStates.waiting_personal_confirm,
        func=lambda call: call.data in {"personal_send", "personal_cancel"},
    )
    @safe_cb
    def process_personal_confirm(call):
        """Подтверждение или отмена личного сообщения."""
        if call.data == "personal_cancel":
            bot.delete_state(call.from_user.id, call.message.chat.id)
            bot.answer_callback_query(call.id, "❌ Отменено")
            bot.send_message(
                call.message.chat.id,
                "Отправка отменена.",
                reply_markup=get_admin_menu_keyboard(),
            )
            return

        bot.answer_callback_query(call.id, "⏳ Отправка...")
        asyncio.run(_send_personal_message_async(call))

    async def _send_personal_message_async(call):
        """Async реализация отправки личного сообщения."""
        admin_user = await get_admin_or_error(
            api_client,
            bot,
            call.from_user.id,
            call.message.chat.id,
        )
        if not admin_user:
            return

        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            text = data.get("personal_text")
            telegram_id = data.get("target_telegram_id")

        if not text or not telegram_id:
            bot.send_message(call.message.chat.id, "❌ Данные для отправки не найдены.")
            return

        try:
            bot.send_message(telegram_id, text)
            result_text = "✅ Сообщение отправлено."
        except Exception as e:
            logger.error(f"Не удалось отправить личное сообщение пользователю {telegram_id}: {e}")
            result_text = "❌ Не удалось отправить сообщение."

        bot.delete_state(call.from_user.id, call.message.chat.id)
        bot.send_message(
            call.message.chat.id,
            result_text,
            reply_markup=get_admin_menu_keyboard(),
        )

    @bot.message_handler(state=AdminStates.waiting_broadcast_text, content_types=["text"])
    @safe
    def process_broadcast_text(message: Message):
        """Обработка текста рассылки."""
        if message.text and message.text.startswith("/"):
            return
        text = (message.text or "").strip()
        if not text:
            bot.send_message(message.chat.id, "❌ Введите текст рассылки")
            return

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["broadcast_text"] = text

        bot.set_state(message.from_user.id, AdminStates.waiting_broadcast_confirm, message.chat.id)
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("✅ Отправить", callback_data="broadcast_send"),
            InlineKeyboardButton("❌ Отмена", callback_data="broadcast_cancel"),
        )
        bot.send_message(
            message.chat.id,
            f"📣 <b>Предпросмотр рассылки</b>\n\n{text}",
            reply_markup=keyboard,
        )

    @bot.callback_query_handler(
        state=AdminStates.waiting_broadcast_confirm,
        func=lambda call: call.data in {"broadcast_send", "broadcast_cancel"},
    )
    @safe_cb
    def process_broadcast_confirm(call):
        """Подтверждение или отмена рассылки."""
        if call.data == "broadcast_cancel":
            bot.delete_state(call.from_user.id, call.message.chat.id)
            bot.answer_callback_query(call.id, "❌ Отменено")
            bot.send_message(
                call.message.chat.id,
                "Рассылка отменена.",
                reply_markup=get_admin_menu_keyboard(),
            )
            return

        bot.answer_callback_query(call.id, "⏳ Отправка...")
        asyncio.run(_send_broadcast_async(call))

    async def _send_broadcast_async(call):
        """Async реализация отправки рассылки."""
        admin_user = await get_admin_or_error(
            api_client,
            bot,
            call.from_user.id,
            call.message.chat.id,
        )
        if not admin_user:
            return

        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            text = data.get("broadcast_text")

        if not text:
            bot.send_message(call.message.chat.id, "❌ Текст рассылки не найден.")
            return

        broadcast = await api_client.create_broadcast(admin_user["telegram_id"], text)
        broadcast_id = broadcast["id"]
        logger.info(f"📣 Старт рассылки {broadcast_id} от @{call.from_user.username}")

        total_count = 0
        success_count = 0
        fail_count = 0
        skip = 0
        limit = 100

        while True:
            users = await api_client.get_admin_users(
                admin_user["telegram_id"], skip=skip, limit=limit
            )
            if not users:
                break

            for user in users:
                total_count += 1
                telegram_id = user.get("telegram_id")
                if not telegram_id:
                    fail_count += 1
                    continue
                try:
                    bot.send_message(telegram_id, text)
                    success_count += 1
                except Exception as e:
                    fail_count += 1
                    logger.error(f"Не удалось отправить рассылку пользователю {telegram_id}: {e}")

            skip += limit

        await api_client.complete_broadcast(
            admin_user["telegram_id"],
            broadcast_id,
            total_count=total_count,
            success_count=success_count,
            fail_count=fail_count,
        )

        bot.delete_state(call.from_user.id, call.message.chat.id)
        bot.send_message(
            call.message.chat.id,
            "✅ Рассылка завершена.\n"
            f"Всего: {total_count}\n"
            f"Успешно: {success_count}\n"
            f"Ошибок: {fail_count}",
            reply_markup=get_admin_menu_keyboard(),
        )
