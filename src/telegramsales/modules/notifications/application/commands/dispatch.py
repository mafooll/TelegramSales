from dataclasses import dataclass
from datetime import timedelta

from telegramsales.modules.notifications.application.ports import (
    Delivered,
    INotificationSender,
    INotificationsUnitOfWork,
    Postponed,
    Refused,
)
from telegramsales.modules.notifications.contracts import RecipientId
from telegramsales.modules.notifications.domain.entities import Notification
from telegramsales.shared.application.clock import IClock

BATCH_SIZE = 25


@dataclass(frozen=True, slots=True)
class DispatchOutbox:
    limit: int = BATCH_SIZE


class DispatchOutboxHandler:
    def __init__(
        self,
        uow: INotificationsUnitOfWork,
        sender: INotificationSender,
        clock: IClock,
    ) -> None:
        self._uow: INotificationsUnitOfWork = uow
        self._sender: INotificationSender = sender
        self._clock: IClock = clock

    async def handle(self, command: DispatchOutbox) -> int:
        async with self._uow as uow:
            claimed = await uow.outbox.claim(command.limit, self._clock.now())

        for notification in claimed:
            await self._deliver(notification)
        return len(claimed)

    async def _deliver(self, notification: Notification) -> None:
        delivery = await self._sender.send(notification)
        match delivery:
            case Delivered():
                notification.sent()
            case Postponed(seconds):
                notification.postponed(
                    until=self._clock.now() + timedelta(seconds=seconds)
                )
            case Refused(reason):
                notification.rejected(reason=reason)

        async with self._uow as uow:
            await uow.outbox.save(notification)
            if isinstance(delivery, Refused):
                await self._unsubscribe(uow, notification.recipient_id)

    @staticmethod
    async def _unsubscribe(
        uow: INotificationsUnitOfWork,
        recipient_id: RecipientId,
    ) -> None:
        subscription = await uow.subscriptions.get(recipient_id)
        if subscription is None or not subscription.is_on:
            return

        subscription.switch(enabled=False)
        await uow.subscriptions.save(subscription)
