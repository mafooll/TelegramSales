from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from dishka import AsyncContainer, make_async_container
from dishka.integrations.aiogram import AiogramProvider

from telegramsales.apps.bot.provider import BotProvider
from telegramsales.modules.catalog import CatalogProvider
from telegramsales.modules.staff import StaffProvider
from telegramsales.shared.provider import SharedProvider


@asynccontextmanager
async def container_context() -> AsyncGenerator[AsyncContainer]:
    container = make_async_container(
        SharedProvider(),
        BotProvider(),
        CatalogProvider(),
        StaffProvider(),
        AiogramProvider(),
    )
    try:
        yield container
    finally:
        await container.close()
