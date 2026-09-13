from dataclasses import dataclass

from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.desk.application.conversations import Conversations
from telegramsales.modules.desk.application.ports import IWorkChat
from telegramsales.modules.desk.application.topics import Topics


@dataclass(frozen=True, slots=True)
class CallForSupport:
    customer_id: CustomerId


class CallForSupportHandler:
    def __init__(
        self,
        topics: Topics,
        work_chat: IWorkChat,
        conversations: Conversations,
    ) -> None:
        self._topics: Topics = topics
        self._work_chat: IWorkChat = work_chat
        self._conversations: Conversations = conversations

    async def handle(self, command: CallForSupport) -> bool:
        if await self._conversations.is_blocked(command.customer_id):
            return False

        thread_id = await self._topics.of_customer(command.customer_id)
        if thread_id is None:
            return False

        await self._work_chat.announce_support(thread_id)
        return True
