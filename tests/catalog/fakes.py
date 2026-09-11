from datetime import datetime
from enum import StrEnum
from types import TracebackType
from typing import Self, override

from telegramsales.modules.catalog.application.ports import (
    IBrandRepository,
    ICatalogRepository,
    ICategoryRepository,
)
from telegramsales.modules.catalog.contracts import (
    BrandId,
    CatalogId,
    CategoryId,
)
from telegramsales.modules.catalog.domain.entities import Brand, Catalog, Category
from telegramsales.modules.catalog.domain.values import Title
from telegramsales.shared.application.access import Actor
from telegramsales.shared.application.clock import IClock
from telegramsales.shared.domain.event import DomainEvent, IEventSource

FIRST_ID = 1000


class FakeCatalogRepository(ICatalogRepository):
    def __init__(self, *catalogs: Catalog) -> None:
        self.items: dict[CatalogId, Catalog] = {item.id: item for item in catalogs}
        self._next: int = FIRST_ID

    @override
    async def next_id(self) -> CatalogId:
        self._next += 1
        return CatalogId(self._next)

    @override
    async def get(self, catalog_id: CatalogId) -> Catalog | None:
        return self.items.get(catalog_id)

    @override
    async def add(self, catalog: Catalog) -> None:
        self.items[catalog.id] = catalog

    @override
    async def save(self, catalog: Catalog) -> None:
        self.items[catalog.id] = catalog

    @override
    async def delete(self, catalog: Catalog) -> None:
        self.items.pop(catalog.id, None)

    @override
    async def exists_with_title(
        self,
        title: Title,
        *,
        excluding: CatalogId | None = None,
    ) -> bool:
        return any(
            item.title == title and item.id != excluding
            for item in self.items.values()
        )


class FakeCategoryRepository(ICategoryRepository):
    def __init__(self, *categories: Category) -> None:
        self.items: dict[CategoryId, Category] = {
            item.id: item for item in categories
        }
        self._next: int = FIRST_ID

    @override
    async def next_id(self) -> CategoryId:
        self._next += 1
        return CategoryId(self._next)

    @override
    async def get(self, category_id: CategoryId) -> Category | None:
        return self.items.get(category_id)

    @override
    async def add(self, category: Category) -> None:
        self.items[category.id] = category

    @override
    async def save(self, category: Category) -> None:
        self.items[category.id] = category

    @override
    async def delete(self, category: Category) -> None:
        self.items.pop(category.id, None)

    @override
    async def count_in_catalog(self, catalog_id: CatalogId) -> int:
        return sum(
            1 for item in self.items.values() if item.catalog_id == catalog_id
        )

    @override
    async def count_children(self, category_id: CategoryId) -> int:
        return sum(
            1 for item in self.items.values() if item.parent_id == category_id
        )

    @override
    async def exists_with_title(
        self,
        title: Title,
        *,
        catalog_id: CatalogId,
        parent_id: CategoryId | None,
        excluding: CategoryId | None = None,
    ) -> bool:
        return any(
            item.title == title
            and item.catalog_id == catalog_id
            and item.parent_id == parent_id
            and item.id != excluding
            for item in self.items.values()
        )


class FakeBrandRepository(IBrandRepository):
    def __init__(self, *brands: Brand) -> None:
        self.items: dict[BrandId, Brand] = {item.id: item for item in brands}
        self._next: int = FIRST_ID

    @override
    async def next_id(self) -> BrandId:
        self._next += 1
        return BrandId(self._next)

    @override
    async def get(self, brand_id: BrandId) -> Brand | None:
        return self.items.get(brand_id)

    @override
    async def add(self, brand: Brand) -> None:
        self.items[brand.id] = brand

    @override
    async def save(self, brand: Brand) -> None:
        self.items[brand.id] = brand

    @override
    async def delete(self, brand: Brand) -> None:
        self.items.pop(brand.id, None)

    @override
    async def exists_with_title(
        self,
        title: Title,
        *,
        excluding: BrandId | None = None,
    ) -> bool:
        return any(
            item.title == title and item.id != excluding
            for item in self.items.values()
        )


class FakeCatalogUnitOfWork:
    def __init__(
        self,
        *,
        catalogs: FakeCatalogRepository | None = None,
        categories: FakeCategoryRepository | None = None,
        brands: FakeBrandRepository | None = None,
    ) -> None:
        self._catalogs: FakeCatalogRepository = catalogs or FakeCatalogRepository()
        self._categories: FakeCategoryRepository = (
            categories or FakeCategoryRepository()
        )
        self._brands: FakeBrandRepository = brands or FakeBrandRepository()
        self._tracked: list[IEventSource] = []
        self.committed: bool = False
        self.rolled_back: bool = False

    @property
    def catalogs(self) -> FakeCatalogRepository:
        return self._catalogs

    @property
    def categories(self) -> FakeCategoryRepository:
        return self._categories

    @property
    def brands(self) -> FakeBrandRepository:
        return self._brands

    async def __aenter__(self) -> Self:
        self._tracked = []
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type is None:
            self.committed = True
        else:
            self.rolled_back = True

    def track(self, entity: IEventSource) -> None:
        self._tracked.append(entity)

    def collect_events(self) -> list[DomainEvent]:
        return []


class FixedClock(IClock):
    def __init__(self, moment: datetime) -> None:
        self._moment: datetime = moment

    @override
    def now(self) -> datetime:
        return self._moment


def actor_with(*permissions: StrEnum, actor_id: int = 100) -> Actor:
    return Actor(
        id=actor_id,
        permissions=frozenset(permission.value for permission in permissions),
    )
