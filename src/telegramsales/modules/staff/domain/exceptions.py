from telegramsales.modules.staff.contracts import StaffId
from telegramsales.modules.staff.domain.enums import StaffRole
from telegramsales.shared.domain.exceptions import DomainError


class RoleAlreadyAssignedError(DomainError):
    def __init__(self, *, staff_id: StaffId, role: StaffRole) -> None:
        super().__init__(
            f"staff member {staff_id} already has role {role}",
            details={"staff_id": staff_id, "role": role},
        )


class AccessAlreadyGrantedError(DomainError):
    def __init__(self, *, staff_id: StaffId) -> None:
        super().__init__(
            f"staff member {staff_id} already has access",
            details={"staff_id": staff_id},
        )


class AccessAlreadyRevokedError(DomainError):
    def __init__(self, *, staff_id: StaffId) -> None:
        super().__init__(
            f"access of staff member {staff_id} is already revoked",
            details={"staff_id": staff_id},
        )


class InactiveStaffMemberError(DomainError):
    def __init__(self, *, staff_id: StaffId) -> None:
        super().__init__(
            f"staff member {staff_id} has no access and cannot be modified",
            details={"staff_id": staff_id},
        )


class LastOwnerRevokedError(DomainError):
    def __init__(self, *, staff_id: StaffId) -> None:
        super().__init__(
            f"staff member {staff_id} is the last active owner",
            details={"staff_id": staff_id},
        )
