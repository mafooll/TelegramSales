from datetime import date
from decimal import Decimal
from typing import final
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Date,
    ForeignKey,
    Identity,
    Integer,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from telegramsales.modules.orders.domain.enums import OrderStatus
from telegramsales.modules.orders.domain.values import MAX_COMMENT_LENGTH
from telegramsales.shared.domain.contacts import (
    MAX_ADDRESS_LENGTH,
    MAX_NAME_LENGTH,
    MAX_PHONE_DIGITS,
)
from telegramsales.shared.domain.money import Currency
from telegramsales.shared.infrastructure.database.base import BaseORM
from telegramsales.shared.infrastructure.database.mixins import WithCreatedAtMixin
from telegramsales.shared.infrastructure.database.types import enum_check

TITLE_SNAPSHOT_LENGTH = 64
ARTICLE_SNAPSHOT_LENGTH = 16
PHONE_LENGTH = MAX_PHONE_DIGITS + 1
STATUS_LENGTH = 16
CURRENCY_LENGTH = 3
PRICE_PRECISION = 12
PRICE_SCALE = 2
DEFAULT_POSITION = "0"


@final
class CartItemORM(WithCreatedAtMixin, BaseORM):
    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint(
            "customer_id",
            "product_id",
            "variant_id",
            postgresql_nulls_not_distinct=True,
        ),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("customers.id", ondelete="CASCADE"),
        index=True,
    )
    product_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
    )
    variant_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("product_variants.id", ondelete="CASCADE"),
    )
    quantity: Mapped[int] = mapped_column(SmallInteger)


@final
class SelectionORM(WithCreatedAtMixin, BaseORM):
    __tablename__ = "selections"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    author_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("customers.id", ondelete="CASCADE"),
        index=True,
    )


@final
class SelectionLineORM(BaseORM):
    __tablename__ = "selection_lines"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    selection_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("selections.id", ondelete="CASCADE"),
        index=True,
    )
    product_id: Mapped[UUID] = mapped_column(Uuid)
    variant_id: Mapped[int | None] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(TITLE_SNAPSHOT_LENGTH))
    variant_title: Mapped[str | None] = mapped_column(
        String(TITLE_SNAPSHOT_LENGTH)
    )
    quantity: Mapped[int] = mapped_column(SmallInteger)
    position: Mapped[int] = mapped_column(
        SmallInteger,
        server_default=DEFAULT_POSITION,
    )


@final
class OrderORM(WithCreatedAtMixin, BaseORM):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("order_date", "sequence"),
        enum_check("status", OrderStatus, name="known_status"),
        enum_check("currency", Currency, name="known_currency"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("customers.id", ondelete="RESTRICT"),
        index=True,
    )
    order_date: Mapped[date] = mapped_column(Date, index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(STATUS_LENGTH), index=True)
    contact_name: Mapped[str] = mapped_column(String(MAX_NAME_LENGTH))
    contact_phone: Mapped[str] = mapped_column(String(PHONE_LENGTH))
    contact_address: Mapped[str] = mapped_column(String(MAX_ADDRESS_LENGTH))
    comment: Mapped[str] = mapped_column(String(MAX_COMMENT_LENGTH))
    total: Mapped[Decimal] = mapped_column(Numeric(PRICE_PRECISION, PRICE_SCALE))
    currency: Mapped[str] = mapped_column(String(CURRENCY_LENGTH))


@final
class OrderLineORM(BaseORM):
    __tablename__ = "order_lines"
    __table_args__ = (enum_check("currency", Currency, name="known_currency"),)

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    order_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("orders.id", ondelete="CASCADE"),
        index=True,
    )
    product_id: Mapped[UUID] = mapped_column(Uuid)
    variant_id: Mapped[int | None] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(TITLE_SNAPSHOT_LENGTH))
    article: Mapped[str] = mapped_column(String(ARTICLE_SNAPSHOT_LENGTH))
    variant_title: Mapped[str | None] = mapped_column(
        String(TITLE_SNAPSHOT_LENGTH)
    )
    price: Mapped[Decimal] = mapped_column(Numeric(PRICE_PRECISION, PRICE_SCALE))
    old_price: Mapped[Decimal | None] = mapped_column(
        Numeric(PRICE_PRECISION, PRICE_SCALE)
    )
    currency: Mapped[str] = mapped_column(String(CURRENCY_LENGTH))
    quantity: Mapped[int] = mapped_column(SmallInteger)
    position: Mapped[int] = mapped_column(
        SmallInteger,
        server_default=DEFAULT_POSITION,
    )
