from enum import StrEnum

from aiogram.filters.callback_data import CallbackData

from telegramsales.modules.staff.domain.enums import StaffRole


class StaffAction(StrEnum):
    LIST = "list"
    CARD = "card"
    ASK_USER = "ask_user"
    SET_ROLE = "set_role"
    RESTORE = "restore"
    ASK_REVOKE = "ask_revoke"
    REVOKE = "revoke"


class StaffCallback(CallbackData, prefix="staff"):
    action: StaffAction
    staff_id: int | None = None
    role: StaffRole | None = None
    page: int = 0
