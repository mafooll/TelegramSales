from typing import final, override

from aiogram import Bot
from aiogram.exceptions import (
    TelegramForbiddenError,
    TelegramRetryAfter,
)

from telegramsales.modules.notifications.application.ports import (
    Delivered,
    Delivery,
    INotificationSender,
    Postponed,
    Refused,
)
from telegramsales.modules.notifications.domain.entities import Notification
from telegramsales.shared.application.i18n import ITranslator


@final
class TelegramSender(INotificationSender):
    def __init__(self, bot: Bot, translate: ITranslator) -> None:
        self._bot: Bot = bot
        self._translate: ITranslator = translate

    @override
    async def send(self, notification: Notification) -> Delivery:
        try:
            await self._bot.send_message(
                chat_id=notification.recipient_id,
                text=self._translate(notification.key, **notification.args),
            )
        except TelegramRetryAfter as error:
            return Postponed(seconds=error.retry_after)
        except TelegramForbiddenError as error:
            return Refused(reason=str(error))
        return Delivered()
