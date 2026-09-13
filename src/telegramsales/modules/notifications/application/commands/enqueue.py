from dataclasses import dataclass

from telegramsales.modules.notifications.application.ports import (
    INotificationsUnitOfWork,
)
from telegramsales.modules.notifications.contracts import (
    NotificationArgs,
    RecipientId,
)
from telegramsales.modules.notifications.domain.entities import NO_ARGS, Notification
from telegramsales.shared.application.clock import IClock


@dataclass(frozen=True, slots=True)
class EnqueueNotification:
    recipient_id: RecipientId
    key: str
    args: NotificationArgs = NO_ARGS
    dedup_key: str | None = None


class EnqueueNotificationHandler:
    def __init__(self, uow: INotificationsUnitOfWork, clock: IClock) -> None:
        self._uow: INotificationsUnitOfWork = uow
        self._clock: IClock = clock

    async def handle(self, command: EnqueueNotification) -> bool:
        async with self._uow as uow:
            notification = Notification.queue(
                notification_id=await uow.outbox.next_id(),
                recipient_id=command.recipient_id,
                key=command.key,
                args=command.args,
                dedup_key=command.dedup_key,
                now=self._clock.now(),
            )
            return await uow.outbox.add(notification)
