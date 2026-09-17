from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Self

from telegramsales.modules.notifications.contracts import (
    CallToAction,
    NotificationArgs,
    NotificationId,
    RecipientId,
)
from telegramsales.modules.notifications.domain.enums import NotificationStatus
from telegramsales.modules.notifications.domain.exceptions import (
    NotificationAlreadyClosedError,
)
from telegramsales.shared.domain.entity import DomainEntity

NO_ARGS: NotificationArgs = MappingProxyType({})
FIRST_ATTEMPT = 1


@dataclass(eq=False, kw_only=True)
class Subscription(DomainEntity[RecipientId]):
    created_at: datetime
    is_on: bool = True

    @classmethod
    def open(cls, *, recipient_id: RecipientId, now: datetime) -> Self:
        return cls(id=recipient_id, created_at=now)

    def switch(self, *, enabled: bool) -> None:
        self.is_on = enabled


@dataclass(eq=False, kw_only=True)
class Notification(DomainEntity[NotificationId]):
    recipient_id: RecipientId
    key: str
    args: NotificationArgs = NO_ARGS
    photo_id: str | None = None
    action: CallToAction | None = None
    dedup_key: str | None = None
    status: NotificationStatus = NotificationStatus.PENDING
    attempts: int = 0
    available_at: datetime
    created_at: datetime
    reason: str | None = None

    @classmethod
    def queue(  # noqa: PLR0913
        cls,
        *,
        notification_id: NotificationId,
        recipient_id: RecipientId,
        key: str,
        args: NotificationArgs = NO_ARGS,
        photo_id: str | None = None,
        action: CallToAction | None = None,
        dedup_key: str | None = None,
        now: datetime,
    ) -> Self:
        return cls(
            id=notification_id,
            recipient_id=recipient_id,
            key=key,
            args=args,
            photo_id=photo_id,
            action=action,
            dedup_key=dedup_key,
            available_at=now,
            created_at=now,
        )

    @property
    def is_pending(self) -> bool:
        return self.status is NotificationStatus.PENDING

    def sent(self) -> None:
        self._ensure_pending()
        self.attempts += FIRST_ATTEMPT
        self.status = NotificationStatus.SENT

    def postponed(self, *, until: datetime) -> None:
        self._ensure_pending()
        self.attempts += FIRST_ATTEMPT
        self.available_at = until

    def rejected(self, *, reason: str) -> None:
        self._ensure_pending()
        self.attempts += FIRST_ATTEMPT
        self.status = NotificationStatus.REJECTED
        self.reason = reason

    def _ensure_pending(self) -> None:
        if not self.is_pending:
            raise NotificationAlreadyClosedError(notification_id=self.id)
