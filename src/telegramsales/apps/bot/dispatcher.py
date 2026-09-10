from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dishka import AsyncContainer
from dishka.integrations.aiogram import setup_dishka

from telegramsales.apps.bot.health import router as health_router
from telegramsales.shared.presentation.bot.middlewares import TranslatorMiddleware


def build_dispatcher(container: AsyncContainer) -> Dispatcher:
    dispatcher = Dispatcher(storage=MemoryStorage())
    setup_dishka(container=container, router=dispatcher, auto_inject=True)

    dispatcher.message.outer_middleware(TranslatorMiddleware())
    dispatcher.callback_query.outer_middleware(TranslatorMiddleware())

    dispatcher.include_router(health_router)
    return dispatcher
