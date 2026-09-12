from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from dishka import AsyncContainer, make_async_container
from dishka.integrations.aiogram import AiogramProvider

from telegramsales.apps.bot.provider import BotProvider
from telegramsales.modules.catalog import CatalogProvider
from telegramsales.modules.customers import CustomerProvider
from telegramsales.modules.orders import OrdersProvider
from telegramsales.modules.staff import StaffProvider
from telegramsales.shared.provider import SharedProvider


@asynccontextmanager
async def container_context() -> AsyncGenerator[AsyncContainer]:
    container = make_async_container(
        SharedProvider(),
        BotProvider(),
        CatalogProvider(),
        CustomerProvider(),
        OrdersProvider(),
        StaffProvider(),
        AiogramProvider(),
    )
    try:
        yield container
    finally:
        await container.close()
