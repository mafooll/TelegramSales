from telegramsales.modules.notifications.application.ports import (
    INotificationOutbox,
    ISubscriptionRepository,
)
from telegramsales.modules.notifications.infrastructure.repositories import (
    NotificationOutbox,
    SubscriptionRepository,
)
from telegramsales.shared.infrastructure.database.uow import UnitOfWork


class NotificationsUnitOfWork(UnitOfWork):
    @property
    def outbox(self) -> INotificationOutbox:
        return NotificationOutbox(self.session)

    @property
    def subscriptions(self) -> ISubscriptionRepository:
        return SubscriptionRepository(self.session)
