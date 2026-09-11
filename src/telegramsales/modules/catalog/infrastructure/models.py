from typing import final

from sqlalchemy import ForeignKey, Identity, SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from telegramsales.modules.catalog.domain.values import MAX_TITLE_LENGTH
from telegramsales.shared.infrastructure.database.base import BaseORM
from telegramsales.shared.infrastructure.database.mixins import WithCreatedAtMixin

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
