from telegramsales.modules.notifications.application.ports import (
    INotificationsUnitOfWork,
)
from telegramsales.modules.notifications.contracts import RecipientId


class SubscriptionReader:
    def __init__(self, uow: INotificationsUnitOfWork) -> None:
        self._uow: INotificationsUnitOfWork = uow

    async def state_of(self, recipient_id: RecipientId) -> bool | None:
        async with self._uow as uow:
            subscription = await uow.subscriptions.get(recipient_id)
        return None if subscription is None else subscription.is_on
