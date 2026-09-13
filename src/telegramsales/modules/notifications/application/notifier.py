from typing import final, override

from telegramsales.modules.notifications.application.commands.enqueue import (
    EnqueueNotification,
    EnqueueNotificationHandler,
)
from telegramsales.modules.notifications.contracts import (
    INotifications,
    NotificationArgs,
    RecipientId,
)
from telegramsales.modules.notifications.domain.entities import NO_ARGS


@final
class Notifier(INotifications):
    def __init__(self, enqueue: EnqueueNotificationHandler) -> None:
        self._enqueue: EnqueueNotificationHandler = enqueue

    @override
    async def enqueue(
        self,
        recipient_id: RecipientId,
        key: str,
        args: NotificationArgs | None = None,
        dedup_key: str | None = None,
    ) -> None:
        await self._enqueue.handle(
            EnqueueNotification(
                recipient_id=recipient_id,
                key=key,
                args=NO_ARGS if args is None else args,
                dedup_key=dedup_key,
            )
        )
