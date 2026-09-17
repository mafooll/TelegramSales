from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any, override

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, TelegramObject, User
from dishka.integrations.aiogram import CONTAINER_NAME

from telegramsales.shared.application.i18n import ITranslatorFactory
from telegramsales.shared.presentation.bot.context import RenderContext
from telegramsales.shared.presentation.bot.render import (
    answer_once,
    start_answering,
    stop_answering,
)

if TYPE_CHECKING:
    from aiogram.fsm.context import FSMContext
    from dishka import AsyncContainer

    from telegramsales.shared.application.access import Actor
    from telegramsales.shared.application.i18n import ITranslator


class TranslatorMiddleware(BaseMiddleware):
    @override
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        container: AsyncContainer = data[CONTAINER_NAME]
        translations = await container.get(ITranslatorFactory)
        user: User | None = data.get("event_from_user")

        data["translate"] = translations(user.language_code if user else None)
        return await handler(event, data)


class RenderContextMiddleware(BaseMiddleware):
    @override
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        actor: Actor | None = data.get("actor")
        translate: ITranslator | None = data.get("translate")

        if actor is not None and translate is not None:
            data["context"] = RenderContext(actor=actor, translate=translate)
        return await handler(event, data)


class StateResetMiddleware(BaseMiddleware):
    @override
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        state: FSMContext | None = data.get("state")
        if state is not None:
            await state.set_state(None)
        return await handler(event, data)


class CallbackAnswerMiddleware(BaseMiddleware):
    @override
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, CallbackQuery):
            return await handler(event, data)

        token = start_answering()
        try:
            return await handler(event, data)
        finally:
            await answer_once(event)
            stop_answering(token)
