from enum import StrEnum

from telegramsales.modules.staff.contracts import StaffId
from telegramsales.shared.domain.exceptions import ApplicationError


class PermissionDeniedError(ApplicationError):
    def __init__(self, *, actor_id: int, permission: StrEnum) -> None:
        super().__init__(
            f"actor {actor_id} lacks permission {permission}",
            details={"actor_id": actor_id, "permission": permission},
        )


class StaffMemberNotFoundError(ApplicationError):
    def __init__(self, *, staff_id: StaffId) -> None:
        super().__init__(
            f"staff member {staff_id} is not found",
            details={"staff_id": staff_id},
        )
