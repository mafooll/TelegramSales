from dataclasses import dataclass

from telegramsales.modules.notifications.application.ports import (
    INotificationsUnitOfWork,
)
from telegramsales.modules.notifications.contracts import RecipientId
from telegramsales.modules.notifications.domain.entities import Subscription
from telegramsales.shared.application.clock import IClock


@dataclass(frozen=True, slots=True)
class OpenSubscription:
    recipient_id: RecipientId


@dataclass(frozen=True, slots=True)
class SwitchSubscription:
    recipient_id: RecipientId
    enabled: bool


class OpenSubscriptionHandler:
    def __init__(self, uow: INotificationsUnitOfWork, clock: IClock) -> None:
        self._uow: INotificationsUnitOfWork = uow
        self._clock: IClock = clock

    async def handle(self, command: OpenSubscription) -> bool:
        async with self._uow as uow:
            if await uow.subscriptions.get(command.recipient_id):
                return False

            await uow.subscriptions.add(
                Subscription.open(
                    recipient_id=command.recipient_id,
                    now=self._clock.now(),
                )
            )
            return True


class SwitchSubscriptionHandler:
    def __init__(self, uow: INotificationsUnitOfWork) -> None:
        self._uow: INotificationsUnitOfWork = uow

    async def handle(self, command: SwitchSubscription) -> bool:
        async with self._uow as uow:
            subscription = await uow.subscriptions.get(command.recipient_id)
            if subscription is None:
                return False

            subscription.switch(enabled=command.enabled)
            await uow.subscriptions.save(subscription)
            return subscription.is_on
