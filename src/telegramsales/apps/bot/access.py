from collections.abc import Mapping
from typing import final, override

from telegramsales.modules.staff.domain.enums import StaffRole
from telegramsales.modules.staff.domain.permissions import StaffPermission
from telegramsales.shared.application.access import (
    IPermissionResolver,
    PermissionCode,
)

ROLE_PERMISSIONS: Mapping[str, frozenset[PermissionCode]] = {
    StaffRole.OWNER: frozenset(permission.value for permission in StaffPermission),
    StaffRole.MANAGER: frozenset({StaffPermission.VIEW_STAFF.value}),
}


@final
class StaticPermissionResolver(IPermissionResolver):
    @override
    def permissions_of(self, role: str) -> frozenset[PermissionCode]:
        return ROLE_PERMISSIONS.get(role, frozenset())
