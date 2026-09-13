from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import NewType

NotificationId = NewType("NotificationId", int)
RecipientId = NewType("RecipientId", int)

type NotificationArgs = Mapping[str, str | int]


class INotifications(ABC):
    @abstractmethod
    async def enqueue(
        self,
        recipient_id: RecipientId,
        key: str,
        args: NotificationArgs | None = None,
        dedup_key: str | None = None,
    ) -> None: ...
