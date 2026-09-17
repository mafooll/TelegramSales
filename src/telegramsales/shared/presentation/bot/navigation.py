from aiogram.filters.callback_data import CallbackData

from telegramsales.shared.presentation.bot import texts
from telegramsales.shared.presentation.bot.keyboard import Button, label


class HomeCallback(CallbackData, prefix="home"):
    pass


def home_button[ViewType]() -> Button[ViewType]:
    return Button(text=label(texts.HOME), callback=lambda _: HomeCallback())
