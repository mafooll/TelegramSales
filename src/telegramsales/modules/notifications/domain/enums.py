from enum import StrEnum


class NotificationStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    REJECTED = "rejected"
