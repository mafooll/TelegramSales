from collections.abc import Awaitable, Callable

from telegramsales.modules.customers.contracts import CustomerId, ICustomerDirectory
from telegramsales.modules.desk.application.exceptions import TopicGoneError
from telegramsales.modules.desk.application.ports import IDeskUnitOfWork, IWorkChat
from telegramsales.modules.desk.contracts import ThreadId
from telegramsales.modules.desk.domain.entities import Topic
from telegramsales.modules.desk.domain.enums import TopicKind

UNNAMED_CUSTOMER = ""


class Topics:
    def __init__(
        self,
        uow: IDeskUnitOfWork,
        work_chat: IWorkChat,
        directory: ICustomerDirectory,
    ) -> None:
        self._uow: IDeskUnitOfWork = uow
        self._work_chat: IWorkChat = work_chat
        self._directory: ICustomerDirectory = directory

    async def feed(self) -> ThreadId | None:
        async with self._uow as uow:
            known = await uow.topics.feed()
        if known is not None:
            return known.thread_id
        if not await self._work_chat.is_ready():
            return None

        thread_id = await self._work_chat.open_feed_topic()
        async with self._uow as uow:
            opened = Topic.feed(
                topic_id=await uow.topics.next_id(),
                thread_id=thread_id,
            )
            return (await uow.topics.remember(opened)).thread_id

    async def of_customer(self, customer_id: CustomerId) -> ThreadId | None:
        async with self._uow as uow:
            known = await uow.topics.of_customer(customer_id)
        if known is not None:
            return known.thread_id
        if not await self._work_chat.is_ready():
            return None

        thread_id = await self._open_for(customer_id)
        async with self._uow as uow:
            opened = Topic.of_customer(
                topic_id=await uow.topics.next_id(),
                customer_id=customer_id,
                thread_id=thread_id,
            )
            return (await uow.topics.remember(opened)).thread_id

    async def customer_of(self, thread_id: ThreadId) -> CustomerId | None:
        async with self._uow as uow:
            topic = await uow.topics.by_thread(thread_id)
        return None if topic is None else topic.customer_id

    async def reopen(self, thread_id: ThreadId) -> ThreadId | None:
        async with self._uow as uow:
            topic = await uow.topics.by_thread(thread_id)
        if topic is None:
            return None

        topic.rebind(await self._reopen_thread(topic))
        async with self._uow as uow:
            await uow.topics.save(topic)
        return topic.thread_id

    async def _reopen_thread(self, topic: Topic) -> ThreadId:
        if topic.kind is TopicKind.FEED or topic.customer_id is None:
            return await self._work_chat.open_feed_topic()
        return await self._open_for(topic.customer_id)

    async def _open_for(self, customer_id: CustomerId) -> ThreadId:
        card = await self._directory.find(customer_id)
        return await self._work_chat.open_customer_topic(
            customer_id,
            UNNAMED_CUSTOMER if card is None else card.name,
        )


async def with_topic_recovery[ResultType](
    topics: Topics,
    thread_id: ThreadId,
    action: Callable[[ThreadId], Awaitable[ResultType]],
) -> ResultType:
    try:
        return await action(thread_id)
    except TopicGoneError:
        reopened = await topics.reopen(thread_id)
        if reopened is None:
            raise
        return await action(reopened)
