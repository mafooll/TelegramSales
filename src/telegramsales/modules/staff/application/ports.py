from abc import ABC, abstractmethod
from types import TracebackType
from typing import Protocol, Self

from telegramsales.modules.staff.application.queries import StaffMemberView
from telegramsales.modules.staff.contracts import StaffId
from telegramsales.modules.staff.domain.entities import StaffMember
from telegramsales.modules.staff.domain.enums import StaffRole
from telegramsales.shared.application.pagination import Page
from telegramsales.shared.domain.event import DomainEvent, IEventSource


class IStaffRepository(ABC):
    @abstractmethod
    async def get(self, staff_id: StaffId) -> StaffMember | None: ...

    @abstractmethod
    async def add(self, member: StaffMember) -> None: ...

    @abstractmethod
    async def save(self, member: StaffMember) -> None: ...

    @abstractmethod
    async def count_active_by_role(self, role: StaffRole) -> int: ...


class IStaffUnitOfWork(Protocol):
    @property
    def staff(self) -> IStaffRepository: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None: ...

    def track(self, entity: IEventSource) -> None: ...

    def collect_events(self) -> list[DomainEvent]: ...


class IStaffQueries(ABC):
    @abstractmethod
    async def get(self, staff_id: StaffId) -> StaffMemberView | None: ...

    @abstractmethod
    async def list_page(self, number: int, size: int) -> Page[StaffMemberView]: ...
