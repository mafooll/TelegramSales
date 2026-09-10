from aiogram import Bot, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, InputRichMessage, Message

from telegramsales.apps.bot import texts
from telegramsales.modules.staff.domain.permissions import StaffPermission
from telegramsales.modules.staff.presentation.bot.callbacks import (
    StaffAction,
    StaffCallback,
)
from telegramsales.shared.presentation.bot.context import RenderContext
from telegramsales.shared.presentation.bot.filters import HasActorFilter
from telegramsales.shared.presentation.bot.keyboard import Button, Screen, label
from telegramsales.shared.presentation.bot.navigation import HomeCallback
from telegramsales.shared.presentation.bot.rich import rich_screen

OPEN_STAFF: Button[None] = Button(
    text=label(texts.OPEN_STAFF_BUTTON),
    callback=lambda _: StaffCallback(action=StaffAction.LIST),
    permission=StaffPermission.VIEW_STAFF,
)

MAIN_MENU: Screen[None] = Screen(
    content=label(texts.GREETING),
    buttons=[OPEN_STAFF],
)

router = Router(name="menu")
router.message.filter(HasActorFilter())
router.callback_query.filter(HasActorFilter())


def _main_menu(context: RenderContext) -> InputRichMessage:
    return rich_screen(MAIN_MENU, None, context)


@router.message(CommandStart())
async def start(message: Message, bot: Bot, context: RenderContext) -> None:
    await bot.send_rich_message(
        chat_id=message.chat.id,
        rich_message=_main_menu(context),
    )


@router.callback_query(HomeCallback.filter())
async def open_menu(callback: CallbackQuery, context: RenderContext) -> None:
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(rich_message=_main_menu(context))
