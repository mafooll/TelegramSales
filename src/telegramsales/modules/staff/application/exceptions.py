from telegramsales.modules.staff.contracts import StaffId
from telegramsales.shared.domain.exceptions import ApplicationError


class StaffMemberNotFoundError(ApplicationError):
    def __init__(self, *, staff_id: StaffId) -> None:
        super().__init__(
            f"staff member {staff_id} is not found",
            details={"staff_id": staff_id},
        )
