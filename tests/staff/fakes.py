from datetime import datetime
from enum import StrEnum
from types import TracebackType
from typing import Self, override

from telegramsales.modules.staff.application.ports import IStaffRepository
from telegramsales.modules.staff.contracts import StaffId
from telegramsales.modules.staff.domain.entities import StaffMember
from telegramsales.modules.staff.domain.enums import StaffRole
from telegramsales.shared.application.access import Actor
from telegramsales.shared.application.clock import IClock
from telegramsales.shared.application.events import IEventPublisher
from telegramsales.shared.domain.event import DomainEvent, IEventSource


class FakeStaffRepository(IStaffRepository):
    def __init__(self, *members: StaffMember) -> None:
        self.members: dict[StaffId, StaffMember] = {m.id: m for m in members}
        self.calls: list[str] = []

    @override
    async def get(self, staff_id: StaffId) -> StaffMember | None:
        self.calls.append("get")
        return self.members.get(staff_id)

    @override
    async def add(self, member: StaffMember) -> None:
        self.calls.append("add")
        self.members[member.id] = member

    @override
    async def save(self, member: StaffMember) -> None:
        self.calls.append("save")
        self.members[member.id] = member

    @override
    async def count_active_by_role(self, role: StaffRole) -> int:
        self.calls.append("count_active_by_role")
        return sum(
            1 for m in self.members.values() if m.is_active and m.role is role
        )


class FakeStaffUnitOfWork:
    def __init__(self, *members: StaffMember) -> None:
        self._staff: FakeStaffRepository = FakeStaffRepository(*members)
        self._tracked: list[IEventSource] = []
        self._events: list[DomainEvent] = []
        self.committed: bool = False
        self.rolled_back: bool = False

    @property
    def staff(self) -> IStaffRepository:
        return self._staff

    @property
    def repository(self) -> FakeStaffRepository:
        return self._staff

    async def __aenter__(self) -> Self:
        self._tracked = []
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type is None:
            self._events = [
                event
                for entity in self._tracked
                for event in entity.collect_events()
            ]
            self.committed = True
        else:
            self.rolled_back = True

    def track(self, entity: IEventSource) -> None:
        self._tracked.append(entity)

    def collect_events(self) -> list[DomainEvent]:
        events = self._events
        self._events = []
        return events


class FakeEventPublisher(IEventPublisher):
    def __init__(self) -> None:
        self.published: list[DomainEvent] = []

    @override
    async def publish_all(self, events: list[DomainEvent]) -> None:
        self.published.extend(events)


class FixedClock(IClock):
    def __init__(self, moment: datetime) -> None:
        self._moment: datetime = moment

    @override
    def now(self) -> datetime:
        return self._moment


def actor_with(*permissions: StrEnum, actor_id: int = 100) -> Actor:
    return Actor(
        id=actor_id,
        permissions=frozenset(permission.value for permission in permissions),
    )
