from datetime import datetime
from decimal import Decimal
from typing import final
from uuid import UUID

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    Numeric,
    Sequence,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from telegramsales.modules.catalog.domain.enums import MediaKind
from telegramsales.modules.catalog.domain.values import (
    MAX_DESCRIPTION_LENGTH,
    MAX_TITLE_LENGTH,
)
from telegramsales.shared.domain.money import Currency
from telegramsales.shared.infrastructure.database.base import BaseORM
from telegramsales.shared.infrastructure.database.mixins import WithCreatedAtMixin
from telegramsales.shared.infrastructure.database.types import enum_check

DEFAULT_SORT_ORDER = "0"


@final
class CatalogORM(WithCreatedAtMixin, BaseORM):
    __tablename__ = "catalogs"
    __table_args__ = (UniqueConstraint("title"),)

    id: Mapped[int] = mapped_column(SmallInteger, Identity(), primary_key=True)
    title: Mapped[str] = mapped_column(String(MAX_TITLE_LENGTH))
    sort_order: Mapped[int] = mapped_column(
        SmallInteger,
        server_default=DEFAULT_SORT_ORDER,
    )
    is_active: Mapped[bool] = mapped_column(default=True)


@final
class CategoryORM(WithCreatedAtMixin, BaseORM):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint(
            "catalog_id",
            "parent_id",
            "title",
            postgresql_nulls_not_distinct=True,
        ),
    )

    id: Mapped[int] = mapped_column(SmallInteger, Identity(), primary_key=True)
    catalog_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey("catalogs.id", ondelete="RESTRICT"),
        index=True,
    )
    parent_id: Mapped[int | None] = mapped_column(
        SmallInteger,
        ForeignKey("categories.id", ondelete="RESTRICT"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(MAX_TITLE_LENGTH))
    sort_order: Mapped[int] = mapped_column(
        SmallInteger,
        server_default=DEFAULT_SORT_ORDER,
    )
    is_active: Mapped[bool] = mapped_column(default=True)


@final
class BrandORM(WithCreatedAtMixin, BaseORM):
    __tablename__ = "brands"
    __table_args__ = (UniqueConstraint("title"),)

    id: Mapped[int] = mapped_column(SmallInteger, Identity(), primary_key=True)
    title: Mapped[str] = mapped_column(String(MAX_TITLE_LENGTH))
    sort_order: Mapped[int] = mapped_column(
        SmallInteger,
        server_default=DEFAULT_SORT_ORDER,
    )
    is_active: Mapped[bool] = mapped_column(default=True)


ARTICLE_SEQUENCE = Sequence("product_article_seq", metadata=BaseORM.metadata)
ARTICLE_LENGTH = 16
CURRENCY_LENGTH = 3
KIND_LENGTH = 8
PRICE_PRECISION = 12
PRICE_SCALE = 2


@final
class ProductORM(WithCreatedAtMixin, BaseORM):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("article"),
        enum_check("currency", Currency, name="known_currency"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    catalog_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey("catalogs.id", ondelete="RESTRICT"),
        index=True,
    )
    category_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey("categories.id", ondelete="RESTRICT"),
        index=True,
    )
    brand_id: Mapped[int | None] = mapped_column(
        SmallInteger,
        ForeignKey("brands.id", ondelete="RESTRICT"),
        index=True,
    )
    article: Mapped[str] = mapped_column(String(ARTICLE_LENGTH))
    title: Mapped[str] = mapped_column(String(MAX_TITLE_LENGTH))
    description: Mapped[str] = mapped_column(String(MAX_DESCRIPTION_LENGTH))
    price: Mapped[Decimal] = mapped_column(Numeric(PRICE_PRECISION, PRICE_SCALE))
    old_price: Mapped[Decimal | None] = mapped_column(
        Numeric(PRICE_PRECISION, PRICE_SCALE)
    )
    currency: Mapped[str] = mapped_column(String(CURRENCY_LENGTH))
    variant_label: Mapped[str | None] = mapped_column(String(MAX_TITLE_LENGTH))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_visible: Mapped[bool] = mapped_column(default=True)
    is_in_stock: Mapped[bool] = mapped_column(default=True)


@final
class ProductVariantORM(WithCreatedAtMixin, BaseORM):
    __tablename__ = "product_variants"
    __table_args__ = (
        UniqueConstraint("product_id", "title"),
        enum_check("currency", Currency, name="known_currency"),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    product_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(MAX_TITLE_LENGTH))
    price_override: Mapped[Decimal | None] = mapped_column(
        Numeric(PRICE_PRECISION, PRICE_SCALE)
    )
    currency: Mapped[str] = mapped_column(String(CURRENCY_LENGTH))
    position: Mapped[int] = mapped_column(
        SmallInteger,
        server_default=DEFAULT_SORT_ORDER,
    )
    is_available: Mapped[bool] = mapped_column(default=True)


@final
class ProductMediaORM(WithCreatedAtMixin, BaseORM):
    __tablename__ = "product_media"
    __table_args__ = (enum_check("kind", MediaKind, name="known_kind"),)

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    product_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
    )
    kind: Mapped[str] = mapped_column(String(KIND_LENGTH))
    file_id: Mapped[str] = mapped_column(Text)
    position: Mapped[int] = mapped_column(
        SmallInteger,
        server_default=DEFAULT_SORT_ORDER,
    )
