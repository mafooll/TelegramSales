from aiogram.enums import ButtonStyle

from telegramsales.modules.staff.application.queries import StaffMemberView
from telegramsales.modules.staff.domain.enums import StaffRole
from telegramsales.modules.staff.domain.permissions import StaffPermission
from telegramsales.modules.staff.presentation.bot import texts
from telegramsales.modules.staff.presentation.bot.callbacks import (
    StaffAction,
    StaffCallback,
)
from telegramsales.modules.staff.presentation.bot.views import (
    StaffListView,
    member_label_key,
    role_key,
)
from telegramsales.shared.presentation.bot.keyboard import Button, label

MEMBER_ENTRY: Button[StaffMemberView] = Button(
    text=lambda member, translate: translate(
        member_label_key(member),
        id=str(member.id),
        role=translate(role_key(member)),
    ),
    callback=lambda member: StaffCallback(
        action=StaffAction.CARD,
        staff_id=member.id,
    ),
)

GRANT_ACCESS: Button[StaffListView] = Button(
    text=label(texts.ADD_MEMBER_BUTTON),
    callback=lambda _: StaffCallback(action=StaffAction.ASK_USER),
    permission=StaffPermission.MANAGE_STAFF,
    style=ButtonStyle.PRIMARY,
)

MAKE_OWNER: Button[StaffMemberView] = Button(
    text=label(texts.MAKE_OWNER_BUTTON),
    callback=lambda member: StaffCallback(
        action=StaffAction.SET_ROLE,
        staff_id=member.id,
        role=StaffRole.OWNER,
    ),
    permission=StaffPermission.MANAGE_STAFF,
    when=lambda member: member.is_active and member.role is StaffRole.MANAGER,
)

MAKE_MANAGER: Button[StaffMemberView] = Button(
    text=label(texts.MAKE_MANAGER_BUTTON),
    callback=lambda member: StaffCallback(
        action=StaffAction.SET_ROLE,
        staff_id=member.id,
        role=StaffRole.MANAGER,
    ),
    permission=StaffPermission.MANAGE_STAFF,
    when=lambda member: member.is_active and member.role is StaffRole.OWNER,
)

REVOKE_ACCESS: Button[StaffMemberView] = Button(
    text=label(texts.REVOKE_BUTTON),
    callback=lambda member: StaffCallback(
        action=StaffAction.ASK_REVOKE,
        staff_id=member.id,
    ),
    permission=StaffPermission.MANAGE_STAFF,
    when=lambda member: member.is_active,
    style=ButtonStyle.DANGER,
)

RESTORE_ACCESS: Button[StaffMemberView] = Button(
    text=label(texts.RESTORE_BUTTON),
    callback=lambda member: StaffCallback(
        action=StaffAction.RESTORE,
        staff_id=member.id,
        role=StaffRole.MANAGER,
    ),
    permission=StaffPermission.MANAGE_STAFF,
    when=lambda member: not member.is_active,
    style=ButtonStyle.SUCCESS,
)

BACK_TO_LIST: Button[StaffMemberView] = Button(
    text=label(texts.BACK_TO_LIST_BUTTON),
    callback=lambda _: StaffCallback(action=StaffAction.LIST),
)
