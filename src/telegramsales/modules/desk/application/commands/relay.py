from collections.abc import Sequence
from dataclasses import dataclass
from functools import partial

from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.desk.application.ports import (
    ICustomerChat,
    IDeskUnitOfWork,
    IWorkChat,
)
from telegramsales.modules.desk.application.topics import Topics, with_topic_recovery
from telegramsales.modules.desk.contracts import MessageId, ThreadId
from telegramsales.modules.desk.domain.entities import RelayLink


@dataclass(frozen=True, slots=True)
class RelayToTopic:
    customer_id: CustomerId
    message_ids: Sequence[MessageId]


@dataclass(frozen=True, slots=True)
class RelayToCustomer:
    thread_id: ThreadId
    message_ids: Sequence[MessageId]


@dataclass(frozen=True, slots=True)
class EditFromCustomer:
    customer_id: CustomerId
    message_id: MessageId
    text: str


@dataclass(frozen=True, slots=True)
class EditFromTopic:
    message_id: MessageId
    text: str


@dataclass(frozen=True, slots=True)
class ReactFromCustomer:
    customer_id: CustomerId
    message_id: MessageId
    emoji: str | None


@dataclass(frozen=True, slots=True)
class ReactFromTopic:
    message_id: MessageId
    emoji: str | None


class RelayToTopicHandler:
    def __init__(
        self,
        topics: Topics,
        uow: IDeskUnitOfWork,
        work_chat: IWorkChat,
    ) -> None:
        self._topics: Topics = topics
        self._uow: IDeskUnitOfWork = uow
        self._work_chat: IWorkChat = work_chat

    async def handle(self, command: RelayToTopic) -> None:
        thread_id = await self._topics.of_customer(command.customer_id)
        if thread_id is None:
            return

        for message_id in command.message_ids:
            copied = await with_topic_recovery(
                self._topics,
                thread_id,
                partial(
                    self._work_chat.copy_into,
                    customer_id=command.customer_id,
                    message_id=message_id,
                ),
            )
            await self._remember(command.customer_id, message_id, copied)

    async def _remember(
        self,
        customer_id: CustomerId,
        customer_message_id: MessageId,
        topic_message_id: MessageId,
    ) -> None:
        async with self._uow as uow:
            await uow.relays.add(
                RelayLink(
                    id=await uow.relays.next_id(),
                    customer_id=customer_id,
                    customer_message_id=customer_message_id,
                    topic_message_id=topic_message_id,
                )
            )


class RelayToCustomerHandler:
    def __init__(
        self,
        topics: Topics,
        uow: IDeskUnitOfWork,
        customer_chat: ICustomerChat,
    ) -> None:
        self._topics: Topics = topics
        self._uow: IDeskUnitOfWork = uow
        self._customer_chat: ICustomerChat = customer_chat

    async def handle(self, command: RelayToCustomer) -> None:
        customer_id = await self._topics.customer_of(command.thread_id)
        if customer_id is None:
            return

        for message_id in command.message_ids:
            copied = await self._customer_chat.copy_from_work_chat(
                customer_id,
                message_id,
            )
            async with self._uow as uow:
                await uow.relays.add(
                    RelayLink(
                        id=await uow.relays.next_id(),
                        customer_id=customer_id,
                        customer_message_id=copied,
                        topic_message_id=message_id,
                    )
                )


class EditFromCustomerHandler:
    def __init__(self, uow: IDeskUnitOfWork, work_chat: IWorkChat) -> None:
        self._uow: IDeskUnitOfWork = uow
        self._work_chat: IWorkChat = work_chat

    async def handle(self, command: EditFromCustomer) -> None:
        async with self._uow as uow:
            link = await uow.relays.by_customer_message(
                command.customer_id,
                command.message_id,
            )
        if link is None:
            return

        await self._work_chat.edit_message(link.topic_message_id, command.text)


class EditFromTopicHandler:
    def __init__(self, uow: IDeskUnitOfWork, customer_chat: ICustomerChat) -> None:
        self._uow: IDeskUnitOfWork = uow
        self._customer_chat: ICustomerChat = customer_chat

    async def handle(self, command: EditFromTopic) -> None:
        async with self._uow as uow:
            link = await uow.relays.by_topic_message(command.message_id)
        if link is None:
            return

        await self._customer_chat.edit_message(
            link.customer_id,
            link.customer_message_id,
            command.text,
        )


class ReactFromCustomerHandler:
    def __init__(self, uow: IDeskUnitOfWork, work_chat: IWorkChat) -> None:
        self._uow: IDeskUnitOfWork = uow
        self._work_chat: IWorkChat = work_chat

    async def handle(self, command: ReactFromCustomer) -> None:
        async with self._uow as uow:
            link = await uow.relays.by_customer_message(
                command.customer_id,
                command.message_id,
            )
        if link is None:
            return

        await self._work_chat.react(link.topic_message_id, command.emoji)


class ReactFromTopicHandler:
    def __init__(self, uow: IDeskUnitOfWork, customer_chat: ICustomerChat) -> None:
        self._uow: IDeskUnitOfWork = uow
        self._customer_chat: ICustomerChat = customer_chat

    async def handle(self, command: ReactFromTopic) -> None:
        async with self._uow as uow:
            link = await uow.relays.by_topic_message(command.message_id)
        if link is None:
            return

        await self._customer_chat.react(
            link.customer_id,
            link.customer_message_id,
            command.emoji,
        )
