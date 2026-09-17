from typing import final, override

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InputRichMessage, ReactionTypeEmoji, ReactionTypeUnion
import structlog
from structlog.stdlib import BoundLogger

from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.desk.application.exceptions import TopicGoneError
from telegramsales.modules.desk.application.ports import ICustomerChat, IWorkChat
from telegramsales.modules.desk.contracts import MessageId, ThreadId
from telegramsales.modules.desk.presentation.bot import texts
from telegramsales.modules.desk.presentation.bot.screens import ORDER_CARD
from telegramsales.modules.desk.presentation.bot.views import WORK_CHAT_VIEWER
from telegramsales.modules.orders.contracts import OrderCardView
from telegramsales.shared.application.i18n import ITranslator
from telegramsales.shared.presentation.bot.context import RenderContext
from telegramsales.shared.presentation.bot.rich import rich_screen

logger: BoundLogger = structlog.get_logger()

TOPIC_GONE_MARKERS = ("thread not found", "topic_deleted", "topic deleted")
NOT_MODIFIED = "message is not modified"
NO_TEXT_MARKERS = ("there is no text in the message", "message can't be edited")
MESSAGE_GONE_MARKERS = ("message to react not found", "message to edit not found")
MAX_TOPIC_TITLE_LENGTH = 128


def _is_topic_gone(error: TelegramBadRequest) -> bool:
    message = str(error).lower()
    return any(marker in message for marker in TOPIC_GONE_MARKERS)


def _is_message_gone(error: TelegramBadRequest) -> bool:
    message = str(error).lower()
    return any(marker in message for marker in MESSAGE_GONE_MARKERS)


def _reactions(emoji: str | None) -> list[ReactionTypeUnion] | None:
    return None if emoji is None else [ReactionTypeEmoji(emoji=emoji)]


@final
class TelegramWorkChat(IWorkChat):
    def __init__(
        self,
        bot: Bot,
        chat_id: int,
        translate: ITranslator,
    ) -> None:
        self._bot: Bot = bot
        self._chat_id: int = chat_id
        self._translate: ITranslator = translate
        self._ready: bool = False
        self._complained: bool = False

    @override
    async def is_ready(self) -> bool:
        if self._ready:
            return True

        self._ready = await self._check()
        return self._ready

    async def _check(self) -> bool:
        try:
            chat = await self._bot.get_chat(self._chat_id)
        except TelegramBadRequest:
            return self._refuse("work_chat_unreachable")

        if not chat.is_forum:
            return self._refuse("work_chat_without_topics")

        member = await self._bot.get_chat_member(self._chat_id, self._bot.id)
        if not getattr(member, "can_manage_topics", False):
            return self._refuse("work_chat_without_topic_rights")
        return True

    def _refuse(self, reason: str) -> bool:
        if not self._complained:
            self._complained = True
            logger.error(reason, chat_id=self._chat_id)
        return False

    @override
    async def open_feed_topic(self) -> ThreadId:
        return await self._open(self._translate(texts.FEED_TOPIC))

    @override
    async def open_customer_topic(
        self,
        customer_id: CustomerId,
        name: str,
    ) -> ThreadId:
        return await self._open(
            self._translate(
                texts.CUSTOMER_TOPIC,
                name=name,
                customer=str(customer_id),
            )
        )

    async def _open(self, title: str) -> ThreadId:
        topic = await self._bot.create_forum_topic(
            self._chat_id,
            title[:MAX_TOPIC_TITLE_LENGTH],
        )
        return ThreadId(topic.message_thread_id)

    @override
    async def post_card(
        self,
        thread_id: ThreadId,
        card: OrderCardView,
    ) -> MessageId:
        try:
            posted = await self._bot.send_rich_message(
                chat_id=self._chat_id,
                rich_message=self._card(card),
                message_thread_id=thread_id,
            )
        except TelegramBadRequest as error:
            raise self._translated(error, thread_id) from error
        return MessageId(posted.message_id)

    @override
    async def redraw_card(
        self,
        message_id: MessageId,
        card: OrderCardView,
    ) -> None:
        try:
            await self._bot.edit_message_text(
                chat_id=self._chat_id,
                message_id=message_id,
                rich_message=self._card(card),
            )
        except TelegramBadRequest as error:
            if NOT_MODIFIED in str(error).lower():
                return
            raise self._translated(error, None) from error

    @override
    async def announce_support(self, thread_id: ThreadId) -> None:
        try:
            await self._bot.send_message(
                chat_id=self._chat_id,
                text=self._translate(texts.SUPPORT_CALLED),
                message_thread_id=thread_id,
            )
        except TelegramBadRequest as error:
            raise self._translated(error, thread_id) from error

    @override
    async def copy_into(
        self,
        thread_id: ThreadId,
        customer_id: CustomerId,
        message_id: MessageId,
    ) -> MessageId:
        try:
            copied = await self._bot.copy_message(
                chat_id=self._chat_id,
                from_chat_id=customer_id,
                message_id=message_id,
                message_thread_id=thread_id,
            )
        except TelegramBadRequest as error:
            raise self._translated(error, thread_id) from error
        return MessageId(copied.message_id)

    @override
    async def edit_message(self, message_id: MessageId, text: str) -> None:
        try:
            await self._bot.edit_message_text(
                chat_id=self._chat_id,
                message_id=message_id,
                text=text,
            )
        except TelegramBadRequest as error:
            await self._edit_caption(message_id, text, error)

    async def _edit_caption(
        self,
        message_id: MessageId,
        text: str,
        error: TelegramBadRequest,
    ) -> None:
        if _is_message_gone(error):
            return
        if not any(marker in str(error).lower() for marker in NO_TEXT_MARKERS):
            raise error
        await self._bot.edit_message_caption(
            chat_id=self._chat_id,
            message_id=message_id,
            caption=text,
        )

    @override
    async def react(self, message_id: MessageId, emoji: str | None) -> None:
        try:
            await self._bot.set_message_reaction(
                chat_id=self._chat_id,
                message_id=message_id,
                reaction=_reactions(emoji),
            )
        except TelegramBadRequest as error:
            if not _is_message_gone(error):
                raise

    def _card(self, card: OrderCardView) -> InputRichMessage:
        return rich_screen(
            ORDER_CARD,
            card,
            RenderContext(actor=WORK_CHAT_VIEWER, translate=self._translate),
        )

    @staticmethod
    def _translated(
        error: TelegramBadRequest,
        thread_id: ThreadId | None,
    ) -> Exception:
        if _is_topic_gone(error):
            return TopicGoneError(thread_id=thread_id)
        return error


@final
class TelegramCustomerChat(ICustomerChat):
    def __init__(self, bot: Bot, chat_id: int) -> None:
        self._bot: Bot = bot
        self._chat_id: int = chat_id

    @override
    async def copy_from_work_chat(
        self,
        customer_id: CustomerId,
        message_id: MessageId,
    ) -> MessageId:
        copied = await self._bot.copy_message(
            chat_id=customer_id,
            from_chat_id=self._chat_id,
            message_id=message_id,
        )
        return MessageId(copied.message_id)

    @override
    async def edit_message(
        self,
        customer_id: CustomerId,
        message_id: MessageId,
        text: str,
    ) -> None:
        try:
            await self._bot.edit_message_text(
                chat_id=customer_id,
                message_id=message_id,
                text=text,
            )
        except TelegramBadRequest as error:
            if _is_message_gone(error):
                return
            if not any(marker in str(error).lower() for marker in NO_TEXT_MARKERS):
                raise
            await self._bot.edit_message_caption(
                chat_id=customer_id,
                message_id=message_id,
                caption=text,
            )

    @override
    async def react(
        self,
        customer_id: CustomerId,
        message_id: MessageId,
        emoji: str | None,
    ) -> None:
        try:
            await self._bot.set_message_reaction(
                chat_id=customer_id,
                message_id=message_id,
                reaction=_reactions(emoji),
            )
        except TelegramBadRequest as error:
            if not _is_message_gone(error):
                raise
