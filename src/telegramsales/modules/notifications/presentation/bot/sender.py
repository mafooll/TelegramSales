from typing import final, override

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.types import (
    InputRichBlockButtons,
    InputRichBlockUnion,
    InputRichMessage,
    RichMessageButton,
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
from telegramsales.shared.presentation.bot.content import content_blocks, photo


@final
class TelegramSender(INotificationSender):
    def __init__(self, bot: Bot, translate: ITranslator) -> None:
        self._bot: Bot = bot
        self._translate: ITranslator = translate

    @override
    async def send(self, notification: Notification) -> Delivery:
        try:
            await self._bot.send_rich_message(
                chat_id=notification.recipient_id,
                rich_message=self._message(notification),
            )
        except TelegramRetryAfter as error:
            return Postponed(seconds=error.retry_after)
        except TelegramForbiddenError as error:
            return Refused(reason=str(error))
        return Delivered()

    def _message(self, notification: Notification) -> InputRichMessage:
        text = self._translate(notification.key, **notification.args)
        if notification.photo_id is not None:
            return InputRichMessage(
                blocks=[
                    photo(notification.photo_id, text),
                    *self._action_blocks(notification),
                ]
            )

        return InputRichMessage(
            blocks=[
                *content_blocks(text),
                *self._action_blocks(notification),
            ]
        )

    def _action_blocks(
        self,
        notification: Notification,
    ) -> list[InputRichBlockUnion]:
        action = notification.action
        if action is None:
            return []

        return [
            InputRichBlockButtons(
                buttons=[
                    RichMessageButton(
                        text=self._translate(action.key),
                        callback_data=action.data,
                    )
                ]
            )
        ]
