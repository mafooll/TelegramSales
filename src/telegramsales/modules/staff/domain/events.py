from dataclasses import dataclass

from telegramsales.modules.staff.contracts import StaffId
from telegramsales.modules.staff.domain.enums import StaffRole
from telegramsales.shared.domain.event import DomainEvent


@dataclass(frozen=True, kw_only=True)
class StaffMemberCreated(DomainEvent):
    staff_id: StaffId
    role: StaffRole
    created_by: StaffId


@dataclass(frozen=True, kw_only=True)
class StaffRoleChanged(DomainEvent):
    staff_id: StaffId
    old_role: StaffRole
    new_role: StaffRole
    changed_by: StaffId


@dataclass(frozen=True, kw_only=True)
class StaffAccessGranted(DomainEvent):
    staff_id: StaffId
    role: StaffRole
    granted_by: StaffId


@dataclass(frozen=True, kw_only=True)
class StaffAccessRevoked(DomainEvent):
    staff_id: StaffId
    revoked_by: StaffId
