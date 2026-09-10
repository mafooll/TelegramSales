from aiogram import Router
from aiogram.filters import ExceptionTypeFilter
from aiogram.types import ErrorEvent

from telegramsales.shared.domain.exceptions import BaseError


async def show_domain_error(event: ErrorEvent) -> None:
    callback = event.update.callback_query
    if callback is not None:
        await callback.answer(text=str(event.exception), show_alert=True)
        return
    message = event.update.message
    if message is not None:
        await message.answer(text=str(event.exception))


def report_domain_errors(router: Router) -> None:
    router.error.register(show_domain_error, ExceptionTypeFilter(BaseError))
