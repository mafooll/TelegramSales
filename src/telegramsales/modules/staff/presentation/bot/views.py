from dataclasses import dataclass

from telegramsales.modules.staff.application.queries import StaffMemberView
from telegramsales.modules.staff.domain.enums import StaffRole
from telegramsales.modules.staff.presentation.bot import texts


@dataclass(frozen=True, slots=True)
class StaffListView:
    total: int


ROLE_KEYS = {
    StaffRole.OWNER: texts.ROLE_OWNER,
    StaffRole.MANAGER: texts.ROLE_MANAGER,
}


def member_label_key(member: StaffMemberView) -> str:
    return texts.MEMBER_LABEL if member.is_active else texts.MEMBER_LABEL_REVOKED


def role_key(member: StaffMemberView) -> str:
    return ROLE_KEYS[member.role]
