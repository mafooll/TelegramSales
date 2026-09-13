from dataclasses import dataclass

from telegramsales.modules.notifications.application.ports import (
    INotificationsUnitOfWork,
)
from telegramsales.modules.notifications.contracts import NotificationArgs
from telegramsales.modules.notifications.domain.entities import NO_ARGS, Notification
from telegramsales.shared.application.clock import IClock

DEDUP_SEPARATOR = ":"


@dataclass(frozen=True, slots=True)
class Announce:
    key: str
    args: NotificationArgs = NO_ARGS
    topic: str | None = None


class AnnounceHandler:
    def __init__(self, uow: INotificationsUnitOfWork, clock: IClock) -> None:
        self._uow: INotificationsUnitOfWork = uow
        self._clock: IClock = clock

    async def handle(self, command: Announce) -> int:
        now = self._clock.now()

        async with self._uow as uow:
            recipients = await uow.subscriptions.recipients()
            queued = 0

            for recipient_id in recipients:
                notification = Notification.queue(
                    notification_id=await uow.outbox.next_id(),
                    recipient_id=recipient_id,
                    key=command.key,
                    args=command.args,
                    dedup_key=(
                        None
                        if command.topic is None
                        else f"{command.topic}{DEDUP_SEPARATOR}{recipient_id}"
                    ),
                    now=now,
                )
                queued += await uow.outbox.add(notification)

            return queued
