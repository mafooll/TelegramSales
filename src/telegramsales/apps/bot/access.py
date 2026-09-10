from collections.abc import Mapping
from typing import final, override

from telegramsales.shared.application.access import (
    IPermissionResolver,
    PermissionCode,
)

ROLE_PERMISSIONS: Mapping[str, frozenset[PermissionCode]] = {}


@final
class StaticPermissionResolver(IPermissionResolver):
    @override
    def permissions_of(self, role: str) -> frozenset[PermissionCode]:
        return ROLE_PERMISSIONS.get(role, frozenset())
