from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from telegramsales.modules.catalog.presentation.bot import texts
from telegramsales.shared.application.i18n import ITranslator


def build_cancel_keyboard(translate: ITranslator) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=translate(texts.CANCEL_BUTTON))
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
