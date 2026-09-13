from datetime import datetime
from typing import Any, final

from sqlalchemy import BigInteger, DateTime, Identity, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from telegramsales.modules.notifications.domain.enums import NotificationStatus
from telegramsales.shared.infrastructure.database.base import BaseORM
from telegramsales.shared.infrastructure.database.mixins import WithCreatedAtMixin
from telegramsales.shared.infrastructure.database.types import enum_check

KEY_LENGTH = 64
ACTION_DATA_LENGTH = 64
STATUS_LENGTH = 16
DEDUP_KEY_LENGTH = 128
NO_ATTEMPTS = "0"


@final
class SubscriptionORM(WithCreatedAtMixin, BaseORM):
    __tablename__ = "notification_subscriptions"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=False,
    )
    is_on: Mapped[bool] = mapped_column(default=True, index=True)


@final
class NotificationORM(WithCreatedAtMixin, BaseORM):
    __tablename__ = "outbox_messages"
    __table_args__ = (enum_check("status", NotificationStatus, name="known_status"),)

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    recipient_id: Mapped[int] = mapped_column(BigInteger, index=True)
    key: Mapped[str] = mapped_column(String(KEY_LENGTH))
    args: Mapped[dict[str, Any]] = mapped_column(JSONB)
    action_key: Mapped[str | None] = mapped_column(String(KEY_LENGTH))
    action_data: Mapped[str | None] = mapped_column(String(ACTION_DATA_LENGTH))
    dedup_key: Mapped[str | None] = mapped_column(
        String(DEDUP_KEY_LENGTH),
        unique=True,
    )
    status: Mapped[str] = mapped_column(String(STATUS_LENGTH), index=True)
    attempts: Mapped[int] = mapped_column(Integer, server_default=NO_ATTEMPTS)
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
    )
    reason: Mapped[str | None] = mapped_column(Text)
