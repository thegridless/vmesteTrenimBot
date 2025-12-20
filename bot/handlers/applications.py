"""
Обработчики для работы с заявками на участие.
"""

from loguru import logger
from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from api_client import api_client
from keyboards import get_main_menu_keyboard
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
        user_tg = message.from_user
        logger.info(f"👤 /applications от @{user_tg.username} (id={user_tg.id})")

        user = api_client.get_user_by_telegram_id(user_tg.id)
        if not user:
            bot.send_message(message.chat.id, "❌ Пользователь не найден. Используйте /start")
            return

        try:
            # Получаем созданные события
            created_events = api_client.get_created_events(user["id"])

            if not created_events:
                bot.send_message(
                    message.chat.id,
                    "📭 У вас пока нет созданных тренировок.",
                    reply_markup=get_main_menu_keyboard(),
                )
                return

            # Для каждого события получаем заявки
            has_applications = False
            for event in created_events:
                applications = api_client.get_event_applications(event["id"], status="pending")

                if applications:
                    has_applications = True
                    for app in applications:
                        applicant = api_client.get_user_by_id(app["user_id"])
                        if applicant:
                            text = "<b>📝 Заявка на тренировку:</b>\n"
                            text += f"🏋️ <b>{event['title']}</b>\n\n"
                            text += f"👤 {applicant['first_name']}"
                            if applicant.get("age"):
                                text += f", {applicant['age']} лет"
                            if applicant.get("city"):
                                text += f"\n📍 {applicant['city']}"
                            text += "\n"

                            keyboard = InlineKeyboardMarkup()
                            keyboard.add(
                                InlineKeyboardButton(
                                    "✅ Одобрить",
                                    callback_data=f"approve_{app['id']}",
                                ),
                                InlineKeyboardButton(
                                    "❌ Отклонить",
                                    callback_data=f"reject_{app['id']}",
                                ),
                            )
                            bot.send_message(message.chat.id, text, reply_markup=keyboard)

            if not has_applications:
                bot.send_message(
                    message.chat.id,
                    "✅ Нет новых заявок на ваши тренировки.",
                    reply_markup=get_main_menu_keyboard(),
                )
        except Exception as e:
            logger.error(f"Ошибка при загрузке заявок: {e}")
            bot.send_message(message.chat.id, "❌ Ошибка при загрузке заявок.")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("approve_"))
    @safe_cb
    def approve_application(call):
        """Одобрить заявку."""
        logger.info(
            f"🎯 approve_application вызван для @{call.from_user.username} (id={call.from_user.id}): data={call.data}"
        )
        application_id = int(call.data.replace("approve_", ""))

        try:
            application = api_client.review_application(application_id, "approved")
            event = api_client.get_event(application["event_id"])
            applicant = api_client.get_user_by_id(application["user_id"])

            bot.answer_callback_query(call.id, "✅ Заявка одобрена!")

            # Уведомляем создателя
            bot.send_message(
                call.message.chat.id,
                f"✅ Заявка от {applicant['first_name']} одобрена!\n" f"Событие: {event['title']}",
            )

            # Уведомляем участника
            if applicant and applicant.get("telegram_id"):
                try:
                    creator = api_client.get_user_by_telegram_id(call.from_user.id)
                    if creator:
                        contact_text = (
                            f"🎉 Ваша заявка одобрена!\n\n"
                            f"🏋️ <b>{event['title']}</b>\n"
                            f"📅 {event['date'][:16]}\n\n"
                            f"Свяжитесь с организатором:\n"
                            f"👤 {creator['first_name']}"
                        )
                        if creator.get("username"):
                            contact_text += f" @{creator['username']}"
                        contact_text += f"\n📱 Telegram ID: {creator['telegram_id']}"

                        bot.send_message(applicant["telegram_id"], contact_text)
                except Exception as e:
                    logger.error(f"Ошибка при отправке уведомления участнику: {e}")

        except Exception as e:
            logger.error(f"Ошибка при одобрении заявки: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("reject_"))
    @safe_cb
    def reject_application(call):
        """Отклонить заявку."""
        logger.info(
            f"🎯 reject_application вызван для @{call.from_user.username} (id={call.from_user.id}): data={call.data}"
        )

        try:
            application_id = int(call.data.replace("reject_", ""))
            logger.debug(f"Обработка отклонения заявки ID: {application_id}")

            application = api_client.review_application(application_id, "rejected")
            logger.debug(f"Заявка отклонена через API: {application}")

            applicant = api_client.get_user_by_id(application["user_id"])
            logger.debug(f"Получен заявитель: {applicant}")

            bot.answer_callback_query(call.id, "❌ Заявка отклонена")

            # Обновляем сообщение, чтобы убрать кнопки
            try:
                bot.edit_message_reply_markup(
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=None,
                )
            except Exception as e:
                logger.debug(f"Не удалось обновить сообщение (возможно, уже обновлено): {e}")

            # Уведомляем участника
            if applicant and applicant.get("telegram_id"):
                try:
                    bot.send_message(
                        applicant["telegram_id"],
                        "❌ К сожалению, ваша заявка была отклонена.",
                    )
                    logger.debug(f"Уведомление отправлено участнику {applicant['telegram_id']}")
                except Exception as e:
                    logger.error(f"Ошибка при отправке уведомления: {e}")

        except ValueError as e:
            logger.error(f"Ошибка при парсинге ID заявки: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка: неверный ID заявки")
        except Exception as e:
            logger.error(f"Ошибка при отклонении заявки: {e}", exc_info=True)
            bot.answer_callback_query(call.id, "❌ Ошибка")
