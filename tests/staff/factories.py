from datetime import UTC, datetime

from telegramsales.modules.staff.contracts import StaffId
from telegramsales.modules.staff.domain.entities import StaffMember
from telegramsales.modules.staff.domain.enums import StaffRole

NOW = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)
OWNER = StaffId(100)
MEMBER = StaffId(200)
OTHER = StaffId(300)


def make_member(
    role: StaffRole = StaffRole.MANAGER,
    staff_id: StaffId = MEMBER,
    *,
    is_active: bool = True,
) -> StaffMember:
    member = StaffMember.create(
        staff_id=staff_id,
        role=role,
        created_by=OWNER,
        now=NOW,
    )
    member.is_active = is_active
    member.collect_events()
    return member
