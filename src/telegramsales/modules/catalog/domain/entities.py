from dataclasses import dataclass
from datetime import datetime
from typing import Self

from telegramsales.modules.catalog.contracts import (
    BrandId,
    CatalogId,
    CategoryId,
)
from telegramsales.modules.catalog.domain.values import Title
from telegramsales.shared.domain.entity import DomainEntity

DEFAULT_SORT_ORDER = 0


@dataclass(eq=False, kw_only=True)
class Catalog(DomainEntity[CatalogId]):
    title: Title
    created_at: datetime
    sort_order: int = DEFAULT_SORT_ORDER
    is_active: bool = True

    @classmethod
    def create(
        cls,
        *,
        catalog_id: CatalogId,
        title: Title,
        now: datetime,
    ) -> Self:
        return cls(id=catalog_id, title=title, created_at=now)

    def rename(self, title: Title) -> None:
        self.title = title

    def archive(self) -> None:
        self.is_active = False

    def restore(self) -> None:
        self.is_active = True


@dataclass(eq=False, kw_only=True)
class Category(DomainEntity[CategoryId]):
    catalog_id: CatalogId
    title: Title
    created_at: datetime
    parent_id: CategoryId | None = None
    sort_order: int = DEFAULT_SORT_ORDER
    is_active: bool = True

    @classmethod
    def create(
        cls,
        *,
        category_id: CategoryId,
        catalog_id: CatalogId,
        title: Title,
        now: datetime,
        parent_id: CategoryId | None = None,
    ) -> Self:
        return cls(
            id=category_id,
            catalog_id=catalog_id,
            title=title,
            created_at=now,
            parent_id=parent_id,
        )

    @property
    def is_root(self) -> bool:
        return self.parent_id is None

    def rename(self, title: Title) -> None:
        self.title = title

    def archive(self) -> None:
        self.is_active = False

    def restore(self) -> None:
        self.is_active = True


@dataclass(eq=False, kw_only=True)
class Brand(DomainEntity[BrandId]):
    title: Title
    created_at: datetime
    sort_order: int = DEFAULT_SORT_ORDER
    is_active: bool = True

    @classmethod
    def create(cls, *, brand_id: BrandId, title: Title, now: datetime) -> Self:
        return cls(id=brand_id, title=title, created_at=now)

    def rename(self, title: Title) -> None:
        self.title = title

    def archive(self) -> None:
        self.is_active = False

    def restore(self) -> None:
        self.is_active = True
