from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from aiogram.filters.callback_data import CallbackData

from telegramsales.shared.application.i18n import TranslationArgs
from telegramsales.shared.presentation.bot import texts
from telegramsales.shared.presentation.bot.keyboard import Button, Screen

NO_ARGS: Mapping[str, TranslationArgs] = MappingProxyType({})


@dataclass(frozen=True, slots=True)
class ConfirmationView:
    question_key: str
    confirm: CallbackData
    cancel: CallbackData
    question_args: Mapping[str, TranslationArgs] = NO_ARGS
    confirm_key: str = texts.CONFIRM
    cancel_key: str = texts.CANCEL


CONFIRMATION_SCREEN: Screen[ConfirmationView] = Screen(
    content=lambda view, translate: translate(
        view.question_key, **view.question_args
    ),
    buttons=[
        Button(
            text=lambda view, translate: translate(view.confirm_key),
            callback=lambda view: view.confirm,
        ),
        Button(
            text=lambda view, translate: translate(view.cancel_key),
            callback=lambda view: view.cancel,
        ),
    ],
    row_width=2,
)
