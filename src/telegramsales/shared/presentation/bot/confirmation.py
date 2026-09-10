from dataclasses import dataclass

from aiogram.filters.callback_data import CallbackData

from telegramsales.shared.presentation.bot import texts
from telegramsales.shared.presentation.bot.keyboard import Button, Screen


@dataclass(frozen=True, slots=True)
class ConfirmationView:
    question: str
    confirm: CallbackData
    cancel: CallbackData
    confirm_text: str = texts.CONFIRM
    cancel_text: str = texts.CANCEL


CONFIRMATION_SCREEN: Screen[ConfirmationView] = Screen(
    buttons=[
        Button(
            text=lambda view: view.confirm_text, callback=lambda view: view.confirm
        ),
        Button(
            text=lambda view: view.cancel_text, callback=lambda view: view.cancel
        ),
    ],
    row_width=2,
)
