from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from typing import NewType

NotificationId = NewType("NotificationId", int)
RecipientId = NewType("RecipientId", int)

type NotificationArgs = Mapping[str, str | int]


@dataclass(frozen=True, slots=True)
class CallToAction:
    key: str
    data: str


class INotifications(ABC):
    @abstractmethod
    async def enqueue(
        self,
        recipient_id: RecipientId,
        key: str,
        args: NotificationArgs | None = None,
        dedup_key: str | None = None,
        action: CallToAction | None = None,
    ) -> None: ...
