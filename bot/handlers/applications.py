"""
Обработчики для работы с заявками на участие.
"""

import asyncio

from api_client import api_client
from common import format_application_text, format_event_text, format_user_info
from keyboards import get_main_menu_keyboard
from loguru import logger
from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from utils import safe_callback, safe_handler


def register_applications_handlers(bot: TeleBot):
    """
    Регистрация обработчиков заявок.

    Args:
        bot: Экземпляр TeleBot
    """
    safe = safe_handler(bot)
    safe_cb = safe_callback(bot)

    @bot.message_handler(commands=["applications"])
    @bot.message_handler(func=lambda m: m.text == "📝 Заявки")
    @safe
    def cmd_applications(message: Message):
        """Показать заявки на мои события."""
        asyncio.run(_cmd_applications_async(message))

    async def _cmd_applications_async(message: Message):
        """Async реализация cmd_applications."""
        logger.info(f"📝 Заявки от @{message.from_user.username or message.from_user.id}")

        user = await api_client.get_user_by_telegram_id(message.from_user.id)
        if not user:
            bot.send_message(message.chat.id, "❌ Пользователь не найден. Используйте /start")
            return

        created_events = await api_client.get_created_events(user["id"])
        if not created_events:
            bot.send_message(
                message.chat.id,
                "📭 У вас пока нет созданных тренировок.",
                reply_markup=get_main_menu_keyboard(is_admin=bool(user.get("is_admin"))),
            )
            return

        has_applications = False
        for event in created_events:
            applications = await api_client.get_event_applications(event["id"], status="pending")
            if not applications:
                continue

            has_applications = True
            for app in applications:
                applicant = await api_client.get_user_by_id(app["user_id"])
                if not applicant:
                    continue

                status_raw = (app.get("status") or "pending").lower()
                status_map = {
                    "pending": "⏳ ожидает",
                    "approved": "✅ одобрена",
                    "rejected": "❌ отклонена",
                }
                status_text = status_map.get(status_raw, "⏳ ожидает")
                text = format_application_text(event, applicant, status=status_text)
                keyboard = InlineKeyboardMarkup(row_width=2)
                if status_raw == "approved":
                    keyboard.add(
                        InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{app['id']}"),
                    )
                elif status_raw == "rejected":
                    keyboard.add(
                        InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{app['id']}"),
                    )
                else:
                    keyboard.add(
                        InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{app['id']}"),
                        InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{app['id']}"),
                    )
                bot.send_message(message.chat.id, text, reply_markup=keyboard)

        if not has_applications:
            bot.send_message(
                message.chat.id,
                "✅ Нет новых заявок на ваши тренировки.",
                reply_markup=get_main_menu_keyboard(is_admin=bool(user.get("is_admin"))),
            )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("approve_"))
    @safe_cb
    def approve_application(call):
        """Одобрить заявку."""
        asyncio.run(_approve_application_async(call))

    async def _approve_application_async(call):
        """Async реализация approve_application."""
        application_id = int(call.data.replace("approve_", ""))
        logger.info(f"✅ Одобрение заявки {application_id}")

        application = await api_client.review_application(application_id, "approved")
        event = await api_client.get_event(application["event_id"])
        applicant = await api_client.get_user_by_id(application["user_id"])

        bot.answer_callback_query(call.id, "✅ Заявка одобрена!")
        bot.send_message(
            call.message.chat.id,
            f"✅ Заявка от {applicant['first_name']} одобрена!\nСобытие: {event['title']}",
        )

        # Убираем кнопки
        try:
            bot.edit_message_reply_markup(
                call.message.chat.id, call.message.message_id, reply_markup=None
            )
        except Exception:
            logger.exception("Не удалось удалить кнопки")

        # Уведомляем участника
        if applicant and applicant.get("telegram_id"):
            creator = await api_client.get_user_by_telegram_id(call.from_user.id)
            contact_text = (
                f"🎉 Ваша заявка одобрена!\n\n"
                f"{format_event_text(event)}\n"
                f"Свяжитесь с организатором:\n"
                f"{format_user_info(creator)}"
            )
            try:
                bot.send_message(applicant["telegram_id"], contact_text)
            except Exception as e:
                logger.error(f"Не удалось уведомить участника: {e}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("reject_"))
    @safe_cb
    def reject_application(call):
        """Отклонить заявку."""
        asyncio.run(_reject_application_async(call))

    async def _reject_application_async(call):
        """Async реализация reject_application."""
        application_id = int(call.data.replace("reject_", ""))
        logger.info(f"❌ Отклонение заявки {application_id}")

        application = await api_client.review_application(application_id, "rejected")
        applicant = await api_client.get_user_by_id(application["user_id"])

        bot.answer_callback_query(call.id, "❌ Заявка отклонена")

        # Убираем кнопки
        try:
            bot.edit_message_reply_markup(
                call.message.chat.id, call.message.message_id, reply_markup=None
            )
        except Exception:
            logger.exception("Не удалось удалить кнопки")

        # Уведомляем участника
        if applicant and applicant.get("telegram_id"):
            try:
                bot.send_message(
                    applicant["telegram_id"], "❌ К сожалению, ваша заявка была отклонена."
                )
            except Exception as e:
                logger.error(f"Не удалось уведомить участника: {e}")
