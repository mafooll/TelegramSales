from dataclasses import dataclass
from datetime import datetime
from typing import Self

from telegramsales.modules.staff.contracts import StaffId
from telegramsales.modules.staff.domain.enums import StaffRole
from telegramsales.modules.staff.domain.events import (
    StaffAccessGranted,
    StaffAccessRevoked,
    StaffMemberCreated,
    StaffRoleChanged,
)
from telegramsales.modules.staff.domain.exceptions import (
    AccessAlreadyGrantedError,
    AccessAlreadyRevokedError,
    InactiveStaffMemberError,
    RoleAlreadyAssignedError,
)
from telegramsales.shared.domain.entity import DomainEntity


@dataclass(eq=False, kw_only=True)
class StaffMember(DomainEntity[StaffId]):
    role: StaffRole
    created_at: datetime
    is_active: bool = True
    customer_view: bool = False

    @classmethod
    def create(
        cls,
        *,
        staff_id: StaffId,
        role: StaffRole,
        created_by: StaffId,
        now: datetime,
    ) -> Self:
        member = cls(id=staff_id, role=role, created_at=now)
        member.register_event(
            StaffMemberCreated(staff_id=staff_id, role=role, created_by=created_by)
        )
        return member

    @property
    def is_owner(self) -> bool:
        return self.is_active and self.role is StaffRole.OWNER

    def switch_customer_view(self, *, enabled: bool) -> None:
        if not self.is_active:
            raise InactiveStaffMemberError(staff_id=self.id)

        self.customer_view = enabled

    def change_role(self, new_role: StaffRole, changed_by: StaffId) -> None:
        if not self.is_active:
            raise InactiveStaffMemberError(staff_id=self.id)
        if self.role is new_role:
            raise RoleAlreadyAssignedError(staff_id=self.id, role=new_role)

        old_role = self.role
        self.role = new_role

        self.register_event(
            StaffRoleChanged(
                staff_id=self.id,
                old_role=old_role,
                new_role=self.role,
                changed_by=changed_by,
            )
        )

    def grant_access(self, role: StaffRole, granted_by: StaffId) -> None:
        if self.is_active:
            raise AccessAlreadyGrantedError(staff_id=self.id)

        self.is_active = True
        self.role = role

        self.register_event(
            StaffAccessGranted(staff_id=self.id, role=role, granted_by=granted_by)
        )

    def revoke_access(self, revoked_by: StaffId) -> None:
        if not self.is_active:
            raise AccessAlreadyRevokedError(staff_id=self.id)

        self.is_active = False

        self.register_event(
            StaffAccessRevoked(staff_id=self.id, revoked_by=revoked_by)
        )
