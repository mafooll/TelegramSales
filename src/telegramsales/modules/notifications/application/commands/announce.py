from dataclasses import dataclass

from telegramsales.modules.notifications.application.ports import (
    INotificationsUnitOfWork,
)
from telegramsales.modules.notifications.contracts import (
    CallToAction,
    NotificationArgs,
    RecipientId,
)
from telegramsales.modules.notifications.domain.entities import NO_ARGS, Notification
from telegramsales.shared.application.clock import IClock

DEDUP_SEPARATOR = ":"


@dataclass(frozen=True, slots=True)
class Announce:
    key: str
    args: NotificationArgs = NO_ARGS
    photo_id: str | None = None
    action: CallToAction | None = None
    topic: str | None = None


class AnnounceHandler:
    def __init__(self, uow: INotificationsUnitOfWork, clock: IClock) -> None:
        self._uow: INotificationsUnitOfWork = uow
        self._clock: IClock = clock

    async def handle(self, command: Announce) -> int:
        now = self._clock.now()

        async with self._uow as uow:
            recipients = await uow.subscriptions.recipients()
            if not recipients:
                return 0

            issued = await uow.outbox.next_ids(len(recipients))
            return await uow.outbox.add_all([
                Notification.queue(
                    notification_id=notification_id,
                    recipient_id=recipient_id,
                    key=command.key,
                    args=command.args,
                    photo_id=command.photo_id,
                    action=command.action,
                    dedup_key=self._dedup_key(command.topic, recipient_id),
                    now=now,
                )
                for notification_id, recipient_id in zip(
                    issued, recipients, strict=True
                )
            ])

    @staticmethod
    def _dedup_key(topic: str | None, recipient_id: RecipientId) -> str | None:
        if topic is None:
            return None
        return f"{topic}{DEDUP_SEPARATOR}{recipient_id}"
