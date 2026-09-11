from collections.abc import AsyncIterator
from typing import final

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.base import BaseStorage
from aiogram.fsm.storage.redis import RedisStorage
from dishka import (
    Provider,
    Scope,
    provide,  # pyright: ignore[reportUnknownVariableType]
)

from telegramsales.apps.bot.access import StaticPermissionResolver
from telegramsales.shared.application.access import IPermissionResolver
from telegramsales.shared.settings import BotSettings, RedisSettings


@final
class BotProvider(Provider):
    scope = Scope.APP

    @provide
    def redis_settings(self) -> RedisSettings:
        return RedisSettings()

    @provide
    async def storage(self, settings: RedisSettings) -> AsyncIterator[BaseStorage]:
        storage = RedisStorage.from_url(settings.url)
        yield storage
        await storage.close()

    @provide
    def bot_settings(self) -> BotSettings:
        return BotSettings()  # pyright: ignore[reportCallIssue]

    @provide
    def permission_resolver(self) -> IPermissionResolver:
        return StaticPermissionResolver()

    @provide
    async def bot(self, settings: BotSettings) -> AsyncIterator[Bot]:
        bot = Bot(
            token=settings.token.get_secret_value(),
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        yield bot
        await bot.session.close()
