from typing import override

from aiogram.filters import Filter
from aiogram.types import Message, TelegramObject

from telegramsales.shared.application.access import Actor
from telegramsales.shared.application.i18n import ITranslator

COMMAND_PREFIX = "/"


class HasActorFilter(Filter):
    @override
    async def __call__(
        self,
        _event: TelegramObject,
        actor: Actor | None = None,
    ) -> bool:
        return actor is not None


class PlainTextFilter(Filter):
    @override
    async def __call__(self, message: Message) -> bool:
        return message.text is not None and not message.text.startswith(
            COMMAND_PREFIX
        )


class TranslatedTextFilter(Filter):
    def __init__(self, key: str) -> None:
        self._key: str = key

    @override
    async def __call__(self, message: Message, translate: ITranslator) -> bool:
        return message.text == translate(self._key)
