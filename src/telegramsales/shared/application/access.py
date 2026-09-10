from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum

type PermissionCode = str


@dataclass(frozen=True, slots=True)
class Actor:
    id: int
    permissions: frozenset[PermissionCode]

    def can(self, permission: StrEnum) -> bool:
        return permission.value in self.permissions


class IPermissionResolver(ABC):
    @abstractmethod
    def permissions_of(self, role: str) -> frozenset[PermissionCode]: ...
