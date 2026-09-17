from aiogram import Dispatcher
from aiogram.fsm.storage.base import BaseStorage
from dishka import AsyncContainer
from dishka.integrations.aiogram import setup_dishka

from telegramsales.apps.bot.cart import router as cart_bridge_router
from telegramsales.apps.bot.menu import router as menu_router
from telegramsales.modules.catalog import catalog_router
from telegramsales.modules.desk import desk_router
from telegramsales.modules.orders import orders_router
from telegramsales.modules.staff import ActorMiddleware, staff_router
from telegramsales.shared.presentation.bot.album import AlbumMiddleware
from telegramsales.shared.presentation.bot.middlewares import (
    CallbackAnswerMiddleware,
    RenderContextMiddleware,
    StateResetMiddleware,
    TranslatorMiddleware,
)
from telegramsales.shared.presentation.bot.observability import (
    HandlerLogMiddleware,
    UpdateLogMiddleware,
)


def build_dispatcher(
    container: AsyncContainer,
    storage: BaseStorage,
    *,
    log_payloads: bool = True,
) -> Dispatcher:
    dispatcher = Dispatcher(storage=storage)
    setup_dishka(container=container, router=dispatcher, auto_inject=True)

    dispatcher.update.outer_middleware(
        UpdateLogMiddleware(with_payload=log_payloads)
    )

    for observer in (dispatcher.message, dispatcher.callback_query):
        observer.outer_middleware(HandlerLogMiddleware())
        observer.outer_middleware(TranslatorMiddleware())
        observer.outer_middleware(ActorMiddleware())
        observer.outer_middleware(RenderContextMiddleware())

    dispatcher.callback_query.outer_middleware(CallbackAnswerMiddleware())
    dispatcher.callback_query.outer_middleware(StateResetMiddleware())
    dispatcher.message.outer_middleware(AlbumMiddleware())

    dispatcher.include_router(orders_router)
    dispatcher.include_router(menu_router)
    dispatcher.include_router(cart_bridge_router)
    dispatcher.include_router(catalog_router)
    dispatcher.include_router(staff_router)
    dispatcher.include_router(desk_router)
    return dispatcher
