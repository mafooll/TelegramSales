from aiogram import F, Router
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from dishka.integrations.aiogram import FromDishka

from telegramsales.modules.staff.application.commands.staff_members import (
    GrantStaffAccess,
    GrantStaffAccessHandler,
    RevokeStaffAccess,
    RevokeStaffAccessHandler,
)
from telegramsales.modules.staff.application.ports import IStaffQueries
from telegramsales.modules.staff.contracts import StaffId
from telegramsales.modules.staff.domain.enums import StaffRole
from telegramsales.modules.staff.presentation.bot import texts
from telegramsales.modules.staff.presentation.bot.callbacks import (
    StaffAction,
    StaffCallback,
)
from telegramsales.modules.staff.presentation.bot.keyboards import (
    GRANT_REQUEST_ID,
    build_user_request_keyboard,
)
from telegramsales.modules.staff.presentation.bot.render import render_card
from telegramsales.shared.presentation.bot.confirmation import (
    CONFIRMATION_SCREEN,
    ConfirmationView,
)
from telegramsales.shared.presentation.bot.context import RenderContext
from telegramsales.shared.presentation.bot.filters import TranslatedTextFilter
from telegramsales.shared.presentation.bot.render import show
from telegramsales.shared.presentation.bot.rich import rich_screen

router = Router(name="staff.access")


@router.callback_query(StaffCallback.filter(F.action == StaffAction.ASK_USER))
async def ask_user(callback: CallbackQuery, context: RenderContext) -> None:
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.answer(
            text=context.translate(texts.ASK_USER),
            reply_markup=build_user_request_keyboard(context.translate),
        )


@router.message(F.users_shared.request_id == GRANT_REQUEST_ID)
async def grant_access(
    message: Message,
    context: RenderContext,
    handler: FromDishka[GrantStaffAccessHandler],
) -> None:
    shared = message.users_shared
    if shared is None or not shared.user_ids:
        return

    await handler.handle(
        GrantStaffAccess(
            staff_id=StaffId(shared.user_ids[0]), role=StaffRole.MANAGER
        ),
        context.actor,
    )
    await message.answer(
        text=context.translate(texts.ACCESS_GRANTED),
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(TranslatedTextFilter(texts.CANCEL_BUTTON))
async def cancel_user_request(message: Message, context: RenderContext) -> None:
    await message.answer(
        text=context.translate(texts.CANCELLED),
        reply_markup=ReplyKeyboardRemove(),
    )


@router.callback_query(StaffCallback.filter(F.action == StaffAction.ASK_REVOKE))
async def ask_revoke(
    callback: CallbackQuery,
    callback_data: StaffCallback,
    context: RenderContext,
    queries: FromDishka[IStaffQueries],
) -> None:
    await callback.answer()
    if callback_data.staff_id is None or not isinstance(callback.message, Message):
        return

    member = await queries.get(StaffId(callback_data.staff_id))
    if member is None:
        return

    view = ConfirmationView(
        question_key=texts.REVOKE_QUESTION,
        question_args={"id": str(member.id)},
        confirm=StaffCallback(action=StaffAction.REVOKE, staff_id=member.id),
        cancel=StaffCallback(action=StaffAction.CARD, staff_id=member.id),
    )
    await show(callback, rich_screen(CONFIRMATION_SCREEN, view, context))


@router.callback_query(StaffCallback.filter(F.action == StaffAction.REVOKE))
async def revoke(
    callback: CallbackQuery,
    callback_data: StaffCallback,
    context: RenderContext,
    handler: FromDishka[RevokeStaffAccessHandler],
    queries: FromDishka[IStaffQueries],
) -> None:
    if callback_data.staff_id is None:
        await callback.answer()
        return

    staff_id = StaffId(callback_data.staff_id)
    await handler.handle(RevokeStaffAccess(staff_id=staff_id), context.actor)
    await callback.answer(text=context.translate(texts.ACCESS_REVOKED))

    member = await queries.get(staff_id)
    if member is not None:
        await render_card(callback, member, context)
