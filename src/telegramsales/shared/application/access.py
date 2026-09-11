from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum

from telegramsales.shared.domain.exceptions import ApplicationError

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


class PermissionDeniedError(ApplicationError):
    def __init__(self, *, actor_id: int, permission: StrEnum) -> None:
        super().__init__(
            f"actor {actor_id} lacks permission {permission}",
            details={"actor_id": actor_id, "permission": permission},
        )
