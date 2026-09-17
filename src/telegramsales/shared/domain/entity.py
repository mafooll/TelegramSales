from collections.abc import Hashable
from dataclasses import dataclass, field
from typing import override

from telegramsales.shared.domain.event import DomainEvent


@dataclass(eq=False, kw_only=True)
class DomainEntity[IdType: Hashable]:
    id: IdType
    _events: list[DomainEvent] = field(
        default_factory=list,
        init=False,
        repr=False,
        compare=False,
    )

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.id == other.id

    @override
    def __hash__(self) -> int:
        return hash((type(self), self.id))

    def register_event(self, event: DomainEvent) -> None:
        self._events.append(event)

    def collect_events(self) -> list[DomainEvent]:
        events = self._events.copy()
        self._events.clear()
        return events

    @property
    def has_events(self) -> bool:
        return bool(self._events)
