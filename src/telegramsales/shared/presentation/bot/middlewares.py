from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any, override

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from dishka.integrations.aiogram import CONTAINER_NAME

from telegramsales.shared.application.i18n import ITranslatorFactory

if TYPE_CHECKING:
    from dishka import AsyncContainer


class TranslatorMiddleware(BaseMiddleware):
    @override
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        container: AsyncContainer = data[CONTAINER_NAME]
        translations = await container.get(ITranslatorFactory)
        user: User | None = data.get("event_from_user")

        data["translate"] = translations(user.language_code if user else None)
        return await handler(event, data)
