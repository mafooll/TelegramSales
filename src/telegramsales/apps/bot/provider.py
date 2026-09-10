from collections.abc import AsyncIterator
from typing import final

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dishka import (
    Provider,
    Scope,
    provide,  # pyright: ignore[reportUnknownVariableType]
)

from telegramsales.apps.bot.access import StaticPermissionResolver
from telegramsales.shared.application.access import IPermissionResolver
from telegramsales.shared.settings import AppSettings, BotSettings


@final
class BotProvider(Provider):
    scope = Scope.APP

    @provide
    def app_settings(self) -> AppSettings:
        return AppSettings()

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
