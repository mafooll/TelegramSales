from dataclasses import dataclass
from functools import partial

from telegramsales.modules.desk.application.exceptions import TopicGoneError
from telegramsales.modules.desk.application.ports import IDeskUnitOfWork, IWorkChat
from telegramsales.modules.desk.application.topics import Topics, with_topic_recovery
from telegramsales.modules.desk.contracts import MessageId, ThreadId
from telegramsales.modules.desk.domain.entities import CardLink
from telegramsales.modules.orders.contracts import (
    IOrderCards,
    OrderCardView,
    OrderId,
)


@dataclass(frozen=True, slots=True)
class PublishOrderCard:
    order_id: OrderId


@dataclass(frozen=True, slots=True)
class RedrawOrderCard:
    order_id: OrderId


class PublishOrderCardHandler:
    def __init__(
        self,
        cards: IOrderCards,
        uow: IDeskUnitOfWork,
        topics: Topics,
        work_chat: IWorkChat,
    ) -> None:
        self._cards: IOrderCards = cards
        self._uow: IDeskUnitOfWork = uow
        self._topics: Topics = topics
        self._work_chat: IWorkChat = work_chat

    async def handle(self, command: PublishOrderCard) -> None:
        card = await self._cards.card(command.order_id)
        if card is None:
            return

        async with self._uow as uow:
            link = await uow.cards.get(card.id) or CardLink.of_order(card.id)
        if link.feed_message_id is None:
            posted = await self._post(await self._topics.feed(), card)
            if posted is not None:
                link.published_in_feed(posted)
        if link.topic_message_id is None:
            topic = await self._topics.of_customer(card.customer_id)
            posted = await self._post(topic, card)
            if posted is not None:
                link.published_in_topic(posted)

        async with self._uow as uow:
            await uow.cards.save(link)

    async def _post(
        self,
        thread_id: ThreadId | None,
        card: OrderCardView,
    ) -> MessageId | None:
        if thread_id is None:
            return None
        return await with_topic_recovery(
            self._topics,
            thread_id,
            partial(self._work_chat.post_card, card=card),
        )


class RedrawOrderCardHandler:
    def __init__(
        self,
        cards: IOrderCards,
        uow: IDeskUnitOfWork,
        work_chat: IWorkChat,
        publish: PublishOrderCardHandler,
    ) -> None:
        self._cards: IOrderCards = cards
        self._uow: IDeskUnitOfWork = uow
        self._work_chat: IWorkChat = work_chat
        self._publish: PublishOrderCardHandler = publish

    async def handle(self, command: RedrawOrderCard) -> None:
        card = await self._cards.card(command.order_id)
        async with self._uow as uow:
            link = await uow.cards.get(command.order_id)
        if card is None or link is None:
            return

        if not await self._redraw(link.feed_message_id, card):
            link.forget_feed()
        if not await self._redraw(link.topic_message_id, card):
            link.forget_topic()
        async with self._uow as uow:
            await uow.cards.save(link)

        if not link.is_published:
            await self._publish.handle(PublishOrderCard(order_id=command.order_id))

    async def _redraw(
        self,
        message_id: MessageId | None,
        card: OrderCardView,
    ) -> bool:
        if message_id is None:
            return False
        try:
            await self._work_chat.redraw_card(message_id, card)
        except TopicGoneError:
            return False
        return True
