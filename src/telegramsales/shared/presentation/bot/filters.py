from typing import override

from aiogram.filters import Filter
from aiogram.types import TelegramObject

from telegramsales.shared.application.access import Actor


class HasActorFilter(Filter):
    @override
    async def __call__(
        self,
        _event: TelegramObject,
        actor: Actor | None = None,
    ) -> bool:
        return actor is not None
