from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dishka import AsyncContainer
from dishka.integrations.aiogram import setup_dishka

from telegramsales.apps.bot.menu import router as menu_router
from telegramsales.modules.staff import ActorMiddleware, staff_router
from telegramsales.shared.presentation.bot.middlewares import (
    RenderContextMiddleware,
    TranslatorMiddleware,
)


def build_dispatcher(container: AsyncContainer) -> Dispatcher:
    dispatcher = Dispatcher(storage=MemoryStorage())
    setup_dishka(container=container, router=dispatcher, auto_inject=True)

    for observer in (dispatcher.message, dispatcher.callback_query):
        observer.outer_middleware(TranslatorMiddleware())
        observer.outer_middleware(ActorMiddleware())
        observer.outer_middleware(RenderContextMiddleware())

    dispatcher.include_router(menu_router)
    dispatcher.include_router(staff_router)
    return dispatcher
