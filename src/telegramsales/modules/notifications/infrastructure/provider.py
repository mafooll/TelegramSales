from typing import final

from dishka import (
    Provider,
    Scope,
    provide,  # pyright: ignore[reportUnknownVariableType]
    provide_all,
)

from telegramsales.modules.notifications.application.commands.announce import (
    AnnounceHandler,
)
from telegramsales.modules.notifications.application.commands.dispatch import (
    DispatchOutboxHandler,
)
from telegramsales.modules.notifications.application.commands.enqueue import (
    EnqueueNotificationHandler,
)
from telegramsales.modules.notifications.application.commands.subscriptions import (
    OpenSubscriptionHandler,
    SwitchSubscriptionHandler,
)
from telegramsales.modules.notifications.application.notifier import Notifier
from telegramsales.modules.notifications.application.ports import (
    INotificationsUnitOfWork,
)
from telegramsales.modules.notifications.application.readers import (
    SubscriptionReader,
)
from telegramsales.modules.notifications.contracts import INotifications
from telegramsales.modules.notifications.infrastructure.uow import (
    NotificationsUnitOfWork,
)
from telegramsales.shared.infrastructure.database.manager import DatabaseManager


@final
class NotificationsProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def unit_of_work(self, manager: DatabaseManager) -> INotificationsUnitOfWork:
        return NotificationsUnitOfWork(manager.session)

    @provide
    def notifier(self, enqueue: EnqueueNotificationHandler) -> INotifications:
        return Notifier(enqueue)

    handlers = provide_all(
        EnqueueNotificationHandler,
        DispatchOutboxHandler,
        AnnounceHandler,
        OpenSubscriptionHandler,
        SwitchSubscriptionHandler,
        SubscriptionReader,
    )
