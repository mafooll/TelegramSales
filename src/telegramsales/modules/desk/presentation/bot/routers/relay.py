from collections.abc import Sequence

from aiogram import F, Router
from aiogram.enums import ContentType
from aiogram.filters import StateFilter
from aiogram.types import (
    Message,
    MessageReactionUpdated,
    ReactionTypeEmoji,
    ReactionTypeUnion,
)
from dishka.integrations.aiogram import FromDishka

from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.desk.application.commands.relay import (
    EditFromCustomer,
    EditFromCustomerHandler,
    EditFromTopic,
    EditFromTopicHandler,
    ReactFromCustomer,
    ReactFromCustomerHandler,
    ReactFromTopic,
    ReactFromTopicHandler,
    RelayToCustomer,
    RelayToCustomerHandler,
    RelayToTopic,
    RelayToTopicHandler,
)
from telegramsales.modules.desk.contracts import MessageId, ThreadId
from telegramsales.modules.desk.presentation.bot.filters import (
    HasOrdersFilter,
    InCustomerChatFilter,
    InWorkChatFilter,
)

router = Router(name="desk.relay")

RELAYABLE = {
    ContentType.TEXT,
    ContentType.PHOTO,
    ContentType.VIDEO,
    ContentType.ANIMATION,
    ContentType.DOCUMENT,
    ContentType.AUDIO,
    ContentType.VOICE,
    ContentType.VIDEO_NOTE,
    ContentType.STICKER,
}
COMMAND_PREFIX = r"^/"


def _message_ids(album: Sequence[Message]) -> list[MessageId]:
    return [MessageId(message.message_id) for message in album]


def _emoji(reactions: Sequence[ReactionTypeUnion]) -> str | None:
    for reaction in reactions:
        if isinstance(reaction, ReactionTypeEmoji):
            return reaction.emoji
    return None


@router.message(
    InWorkChatFilter(),
    F.message_thread_id,
    F.content_type.in_(RELAYABLE),
)
async def relay_to_customer(
    message: Message,
    album: list[Message],
    handler: FromDishka[RelayToCustomerHandler],
) -> None:
    if message.message_thread_id is None:
        return

    await handler.handle(
        RelayToCustomer(
            thread_id=ThreadId(message.message_thread_id),
            message_ids=_message_ids(album),
        )
    )


@router.message(
    InCustomerChatFilter(),
    StateFilter(None),
    ~F.text.regexp(COMMAND_PREFIX),
    F.content_type.in_(RELAYABLE),
    HasOrdersFilter(),
)
async def relay_to_topic(
    message: Message,
    album: list[Message],
    handler: FromDishka[RelayToTopicHandler],
) -> None:
    if message.from_user is None:
        return

    await handler.handle(
        RelayToTopic(
            customer_id=CustomerId(message.from_user.id),
            message_ids=_message_ids(album),
        )
    )


@router.edited_message(InWorkChatFilter(), F.message_thread_id)
async def edit_for_customer(
    message: Message,
    handler: FromDishka[EditFromTopicHandler],
) -> None:
    text = message.text or message.caption
    if text is None:
        return

    await handler.handle(
        EditFromTopic(message_id=MessageId(message.message_id), text=text)
    )


@router.edited_message(InCustomerChatFilter())
async def edit_in_topic(
    message: Message,
    handler: FromDishka[EditFromCustomerHandler],
) -> None:
    text = message.text or message.caption
    if text is None or message.from_user is None:
        return

    await handler.handle(
        EditFromCustomer(
            customer_id=CustomerId(message.from_user.id),
            message_id=MessageId(message.message_id),
            text=text,
        )
    )


@router.message_reaction(InWorkChatFilter())
async def react_for_customer(
    reaction: MessageReactionUpdated,
    handler: FromDishka[ReactFromTopicHandler],
) -> None:
    await handler.handle(
        ReactFromTopic(
            message_id=MessageId(reaction.message_id),
            emoji=_emoji(reaction.new_reaction),
        )
    )


@router.message_reaction(InCustomerChatFilter())
async def react_in_topic(
    reaction: MessageReactionUpdated,
    handler: FromDishka[ReactFromCustomerHandler],
) -> None:
    if reaction.user is None:
        return

    await handler.handle(
        ReactFromCustomer(
            customer_id=CustomerId(reaction.user.id),
            message_id=MessageId(reaction.message_id),
            emoji=_emoji(reaction.new_reaction),
        )
    )
