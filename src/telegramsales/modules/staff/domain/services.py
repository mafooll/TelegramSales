from telegramsales.modules.staff.domain.entities import StaffMember
from telegramsales.modules.staff.domain.exceptions import LastOwnerRevokedError

MIN_OWNER_COUNT = 1


def ensure_owner_remains(member: StaffMember, active_owner_count: int) -> None:
    if member.is_owner and active_owner_count <= MIN_OWNER_COUNT:
        raise LastOwnerRevokedError(staff_id=member.id)
