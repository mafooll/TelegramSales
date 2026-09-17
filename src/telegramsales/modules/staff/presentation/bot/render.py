from aiogram.types import CallbackQuery, Message

from telegramsales.modules.staff.application.ports import IStaffQueries
from telegramsales.modules.staff.application.queries import StaffMemberView
from telegramsales.modules.staff.presentation.bot.callbacks import (
    StaffAction,
    StaffCallback,
)
from telegramsales.modules.staff.presentation.bot.screens import (
    MEMBER_CARD,
    STAFF_LIST,
)
from telegramsales.modules.staff.presentation.bot.views import StaffListView
from telegramsales.shared.application.pagination import DEFAULT_PAGE_SIZE
from telegramsales.shared.presentation.bot.context import RenderContext
from telegramsales.shared.presentation.bot.pagination import Pagination
from telegramsales.shared.presentation.bot.render import show
from telegramsales.shared.presentation.bot.rich import rich_paged_screen, rich_screen


def _page_callback(number: int) -> StaffCallback:
    return StaffCallback(action=StaffAction.LIST, page=number)


async def render_list(
    callback: CallbackQuery,
    queries: IStaffQueries,
    context: RenderContext,
    number: int = 0,
) -> None:
    if not isinstance(callback.message, Message):
        return

    page = await queries.list_page(number, DEFAULT_PAGE_SIZE)
    await show(
        callback,
        rich_paged_screen(
            STAFF_LIST,
            Pagination(page=page, callback=_page_callback),
            StaffListView(total=page.total),
            context,
        ),
    )


async def render_card(
    callback: CallbackQuery,
    member: StaffMemberView,
    context: RenderContext,
) -> None:
    if not isinstance(callback.message, Message):
        return

    await show(callback, rich_screen(MEMBER_CARD, member, context))
