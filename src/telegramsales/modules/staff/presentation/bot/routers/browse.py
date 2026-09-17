from aiogram import F, Router
from aiogram.types import CallbackQuery
from dishka.integrations.aiogram import FromDishka

from telegramsales.modules.staff.application.ports import IStaffQueries
from telegramsales.modules.staff.contracts import StaffId
from telegramsales.modules.staff.presentation.bot.callbacks import (
    StaffAction,
    StaffCallback,
)
from telegramsales.modules.staff.presentation.bot.render import (
    render_card,
    render_list,
)
from telegramsales.shared.presentation.bot.context import RenderContext

router = Router(name="staff.browse")


@router.callback_query(StaffCallback.filter(F.action == StaffAction.LIST))
async def show_list(
    callback: CallbackQuery,
    callback_data: StaffCallback,
    context: RenderContext,
    queries: FromDishka[IStaffQueries],
) -> None:
    await render_list(callback, queries, context, callback_data.page)


@router.callback_query(StaffCallback.filter(F.action == StaffAction.CARD))
async def show_card(
    callback: CallbackQuery,
    callback_data: StaffCallback,
    context: RenderContext,
    queries: FromDishka[IStaffQueries],
) -> None:
    if callback_data.staff_id is None:
        return
    member = await queries.get(StaffId(callback_data.staff_id))
    if member is not None:
        await render_card(callback, member, context)
