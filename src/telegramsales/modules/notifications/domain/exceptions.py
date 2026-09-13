from telegramsales.modules.notifications.contracts import NotificationId
from telegramsales.shared.domain.exceptions import DomainError


class NotificationAlreadyClosedError(DomainError):
    def __init__(self, *, notification_id: NotificationId) -> None:
        super().__init__(
            f"notification {notification_id} is already closed",
            details={"notification_id": notification_id},
        )
