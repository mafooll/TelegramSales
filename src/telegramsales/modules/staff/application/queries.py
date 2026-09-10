from dataclasses import dataclass
from datetime import datetime

from telegramsales.modules.staff.contracts import StaffId
from telegramsales.modules.staff.domain.enums import StaffRole


@dataclass(frozen=True, slots=True)
class StaffMemberView:
    id: StaffId
    role: StaffRole
    is_active: bool
    created_at: datetime
