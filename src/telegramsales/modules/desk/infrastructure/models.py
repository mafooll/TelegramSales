from typing import final
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    ForeignKey,
    Identity,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from telegramsales.modules.desk.domain.enums import TopicKind
from telegramsales.shared.infrastructure.database.base import BaseORM
from telegramsales.shared.infrastructure.database.mixins import WithCreatedAtMixin
from telegramsales.shared.infrastructure.database.types import enum_check

KIND_LENGTH = 16


@final
class TopicORM(WithCreatedAtMixin, BaseORM):
    __tablename__ = "desk_topics"
    __table_args__ = (
        UniqueConstraint(
            "kind",
            "customer_id",
            postgresql_nulls_not_distinct=True,
        ),
        enum_check("kind", TopicKind, name="known_kind"),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    kind: Mapped[str] = mapped_column(String(KIND_LENGTH))
    customer_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("customers.id", ondelete="CASCADE"),
    )
    thread_id: Mapped[int] = mapped_column(BigInteger, unique=True)


@final
class CardORM(WithCreatedAtMixin, BaseORM):
    __tablename__ = "desk_cards"

    order_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("orders.id", ondelete="CASCADE"),
        primary_key=True,
    )
    feed_message_id: Mapped[int | None] = mapped_column(BigInteger)
    topic_message_id: Mapped[int | None] = mapped_column(BigInteger)


@final
class RelayORM(WithCreatedAtMixin, BaseORM):
    __tablename__ = "desk_messages"
    __table_args__ = (UniqueConstraint("customer_id", "customer_message_id"),)

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("customers.id", ondelete="CASCADE"),
        index=True,
    )
    customer_message_id: Mapped[int] = mapped_column(BigInteger)
    topic_message_id: Mapped[int] = mapped_column(BigInteger, unique=True)
