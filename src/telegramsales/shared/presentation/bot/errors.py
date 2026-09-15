from collections.abc import Mapping

from aiogram import Router
from aiogram.filters import ExceptionTypeFilter
from aiogram.types import ErrorEvent

from telegramsales.shared.application.i18n import ITranslator
from telegramsales.shared.domain.exceptions import BaseError
from telegramsales.shared.presentation.bot import texts
from telegramsales.shared.presentation.bot.render import answer_once

type ErrorTexts = Mapping[type[BaseError], str]


def error_text(
    error: BaseException,
    known: ErrorTexts,
    translate: ITranslator,
) -> str:
    for kind, key in known.items():
        if isinstance(error, kind):
            return translate(key)
    return translate(texts.REFUSED)


def report_domain_errors(router: Router, known: ErrorTexts | None = None) -> None:
    texts_of_errors: ErrorTexts = known or {}

    async def show_domain_error(
        event: ErrorEvent,
        translate: ITranslator,
    ) -> None:
        told = error_text(event.exception, texts_of_errors, translate)
        callback = event.update.callback_query
        if callback is not None:
            await answer_once(callback, told, alert=True)
            return
        message = event.update.message
        if message is not None:
            await message.answer(text=told)

    router.error.register(show_domain_error, ExceptionTypeFilter(BaseError))
