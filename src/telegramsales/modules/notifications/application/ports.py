from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from types import TracebackType
from typing import Protocol, Self

from telegramsales.modules.notifications.contracts import (
    NotificationId,
    RecipientId,
)
from telegramsales.modules.notifications.domain.entities import (
    Notification,
    Subscription,
)


@dataclass(frozen=True, slots=True)
class Delivered:
    pass


@dataclass(frozen=True, slots=True)
class Postponed:
    seconds: int


@dataclass(frozen=True, slots=True)
class Refused:
    reason: str


type Delivery = Delivered | Postponed | Refused


class INotificationOutbox(ABC):
    @abstractmethod
    async def next_id(self) -> NotificationId: ...

    @abstractmethod
    async def add(self, notification: Notification) -> bool: ...

    @abstractmethod
    async def claim(self, limit: int, now: datetime) -> list[Notification]: ...

    @abstractmethod
    async def save(self, notification: Notification) -> None: ...


class ISubscriptionRepository(ABC):
    @abstractmethod
    async def get(self, recipient_id: RecipientId) -> Subscription | None: ...

    @abstractmethod
    async def add(self, subscription: Subscription) -> None: ...

    @abstractmethod
    async def save(self, subscription: Subscription) -> None: ...

    @abstractmethod
    async def recipients(self) -> list[RecipientId]: ...


class INotificationsUnitOfWork(Protocol):
    @property
    def outbox(self) -> INotificationOutbox: ...

    @property
    def subscriptions(self) -> ISubscriptionRepository: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None: ...


class INotificationSender(ABC):
    @abstractmethod
    async def send(self, notification: Notification) -> Delivery: ...
