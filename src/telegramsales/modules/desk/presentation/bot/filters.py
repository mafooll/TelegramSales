from typing import TYPE_CHECKING, Any, override

from aiogram.enums import ChatType
from aiogram.filters import Filter
from aiogram.types import Chat, TelegramObject, User
from dishka.integrations.aiogram import CONTAINER_NAME

from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.orders.contracts import IOrderPresence
from telegramsales.shared.settings import AppSettings

if TYPE_CHECKING:
    from dishka import AsyncContainer

CHAT_KEY = "event_chat"
USER_KEY = "event_from_user"


class InWorkChatFilter(Filter):
    @override
    async def __call__(self, _event: TelegramObject, **data: Any) -> bool:
        chat: Chat | None = data.get(CHAT_KEY)
        if chat is None:
            return False

        container: AsyncContainer = data[CONTAINER_NAME]
        settings = await container.get(AppSettings)
        return chat.id == settings.work_chat_id


class InCustomerChatFilter(Filter):
    @override
    async def __call__(self, _event: TelegramObject, **data: Any) -> bool:
        chat: Chat | None = data.get(CHAT_KEY)
        return chat is not None and chat.type == ChatType.PRIVATE


class HasOrdersFilter(Filter):
    @override
    async def __call__(self, _event: TelegramObject, **data: Any) -> bool:
        user: User | None = data.get(USER_KEY)
        if user is None:
            return False

        container: AsyncContainer = data[CONTAINER_NAME]
        presence = await container.get(IOrderPresence)
        return await presence.has_orders(CustomerId(user.id))
