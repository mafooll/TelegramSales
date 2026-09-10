from abc import ABC, abstractmethod

from telegramsales.shared.domain.event import DomainEvent


class IEventPublisher(ABC):
    @abstractmethod
    async def publish_all(self, events: list[DomainEvent]) -> None: ...
