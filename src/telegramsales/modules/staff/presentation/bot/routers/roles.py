from aiogram import F, Router
from aiogram.types import CallbackQuery
from dishka.integrations.aiogram import FromDishka

from telegramsales.modules.staff.application.commands import (
    ChangeStaffRole,
    ChangeStaffRoleHandler,
    GrantStaffAccess,
    GrantStaffAccessHandler,
)
from telegramsales.modules.staff.application.ports import IStaffQueries
from telegramsales.modules.staff.contracts import StaffId
from telegramsales.modules.staff.presentation.bot import texts
from telegramsales.modules.staff.presentation.bot.callbacks import (
    StaffAction,
    StaffCallback,
)
from telegramsales.modules.staff.presentation.bot.render import render_card
from telegramsales.shared.presentation.bot.context import RenderContext

router = Router(name="staff.roles")


@router.callback_query(StaffCallback.filter(F.action == StaffAction.SET_ROLE))
async def set_role(
    callback: CallbackQuery,
    callback_data: StaffCallback,
    context: RenderContext,
    handler: FromDishka[ChangeStaffRoleHandler],
    queries: FromDishka[IStaffQueries],
) -> None:
    if callback_data.staff_id is None or callback_data.role is None:
        await callback.answer()
        return

    staff_id = StaffId(callback_data.staff_id)
    await handler.handle(
        ChangeStaffRole(staff_id=staff_id, new_role=callback_data.role),
        context.actor,
    )
    await callback.answer(text=context.translate(texts.ROLE_CHANGED))

    member = await queries.get(staff_id)
    if member is not None:
        await render_card(callback, member, context)


@router.callback_query(StaffCallback.filter(F.action == StaffAction.RESTORE))
async def restore_access(
    callback: CallbackQuery,
    callback_data: StaffCallback,
    context: RenderContext,
    handler: FromDishka[GrantStaffAccessHandler],
    queries: FromDishka[IStaffQueries],
) -> None:
    if callback_data.staff_id is None or callback_data.role is None:
        await callback.answer()
        return

    staff_id = StaffId(callback_data.staff_id)
    await handler.handle(
        GrantStaffAccess(staff_id=staff_id, role=callback_data.role), context.actor
    )
    await callback.answer(text=context.translate(texts.ACCESS_GRANTED))

    member = await queries.get(staff_id)
    if member is not None:
        await render_card(callback, member, context)
