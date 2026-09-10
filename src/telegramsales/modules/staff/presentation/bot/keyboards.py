from aiogram.types import KeyboardButtonRequestUsers, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from telegramsales.modules.staff.presentation.bot import texts
from telegramsales.shared.application.i18n import ITranslator

GRANT_REQUEST_ID = 1


def build_user_request_keyboard(translate: ITranslator) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(
        text=translate(texts.PICK_USER_BUTTON),
        request_users=KeyboardButtonRequestUsers(
            request_id=GRANT_REQUEST_ID,
            user_is_bot=False,
            max_quantity=1,
        ),
    )
    builder.button(text=translate(texts.CANCEL_BUTTON))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
