import asyncio
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any, final, override

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

ALBUM_KEY = "album"
GATHER_DELAY = 0.3


@final
class AlbumMiddleware(BaseMiddleware):
    def __init__(self, delay: float = GATHER_DELAY) -> None:
        self._delay: float = delay
        self._groups: dict[str, list[Message]] = defaultdict(list)

    @override
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        if event.media_group_id is None:
            data[ALBUM_KEY] = [event]
            return await handler(event, data)

        self._groups[event.media_group_id].append(event)
        await asyncio.sleep(self._delay)

        gathered = self._groups.pop(event.media_group_id, None)
        if gathered is None:
            return None

        data[ALBUM_KEY] = sorted(gathered, key=lambda message: message.message_id)
        return await handler(event, data)
