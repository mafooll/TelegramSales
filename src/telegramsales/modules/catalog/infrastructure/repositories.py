from typing import override

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

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
from telegramsales.modules.catalog.infrastructure.filters import parent_filter
from telegramsales.modules.catalog.infrastructure.mappers import (
    BrandMapper,
    CatalogMapper,
    CategoryMapper,
)
from telegramsales.modules.catalog.infrastructure.models import (
    BrandORM,
    CatalogORM,
    CategoryORM,
)
from telegramsales.shared.infrastructure.database.repository import Repository

ID_COLUMN = "id"


async def _next_id(session: AsyncSession, table: str) -> int:
    sequence = func.pg_get_serial_sequence(table, ID_COLUMN)
    return (await session.execute(select(func.nextval(sequence)))).scalar_one()


async def _exists(session: AsyncSession, query: Select[tuple[int]]) -> bool:
    return (await session.execute(query.limit(1))).first() is not None


class CatalogRepository(ICatalogRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session
        self._models: Repository[CatalogORM, int] = Repository(session, CatalogORM)

    @override
    async def next_id(self) -> CatalogId:
        return CatalogId(await _next_id(self._session, CatalogORM.__tablename__))

    @override
    async def get(self, catalog_id: CatalogId) -> Catalog | None:
        model = await self._models.get(catalog_id)
        return CatalogMapper.to_entity(model) if model is not None else None

    @override
    async def add(self, catalog: Catalog) -> None:
        await self._models.add(CatalogMapper.to_model(catalog))

    @override
    async def save(self, catalog: Catalog) -> None:
        await self._models.merge(CatalogMapper.to_model(catalog))

    @override
    async def delete(self, catalog: Catalog) -> None:
        model = await self._models.get(catalog.id)
        if model is not None:
            await self._models.delete(model)

    @override
    async def exists_with_title(
        self,
        title: Title,
        *,
        excluding: CatalogId | None = None,
    ) -> bool:
        query = select(CatalogORM.id).where(CatalogORM.title == title.value)
        if excluding is not None:
            query = query.where(CatalogORM.id != excluding)
        return await _exists(self._session, query)


class CategoryRepository(ICategoryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session
        self._models: Repository[CategoryORM, int] = Repository(session, CategoryORM)

    @override
    async def next_id(self) -> CategoryId:
        return CategoryId(await _next_id(self._session, CategoryORM.__tablename__))

    @override
    async def get(self, category_id: CategoryId) -> Category | None:
        model = await self._models.get(category_id)
        return CategoryMapper.to_entity(model) if model is not None else None

    @override
    async def add(self, category: Category) -> None:
        await self._models.add(CategoryMapper.to_model(category))

    @override
    async def save(self, category: Category) -> None:
        await self._models.merge(CategoryMapper.to_model(category))

    @override
    async def delete(self, category: Category) -> None:
        model = await self._models.get(category.id)
        if model is not None:
            await self._models.delete(model)

    @override
    async def count_in_catalog(self, catalog_id: CatalogId) -> int:
        query = (
            select(func.count())
            .select_from(CategoryORM)
            .where(CategoryORM.catalog_id == catalog_id)
        )
        return (await self._session.execute(query)).scalar_one()

    @override
    async def count_children(self, category_id: CategoryId) -> int:
        query = (
            select(func.count())
            .select_from(CategoryORM)
            .where(CategoryORM.parent_id == category_id)
        )
        return (await self._session.execute(query)).scalar_one()

    @override
    async def exists_with_title(
        self,
        title: Title,
        *,
        catalog_id: CatalogId,
        parent_id: CategoryId | None,
        excluding: CategoryId | None = None,
    ) -> bool:
        query = select(CategoryORM.id).where(
            CategoryORM.catalog_id == catalog_id,
            parent_filter(parent_id),
            CategoryORM.title == title.value,
        )
        if excluding is not None:
            query = query.where(CategoryORM.id != excluding)
        return await _exists(self._session, query)


class BrandRepository(IBrandRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session
        self._models: Repository[BrandORM, int] = Repository(session, BrandORM)

    @override
    async def next_id(self) -> BrandId:
        return BrandId(await _next_id(self._session, BrandORM.__tablename__))

    @override
    async def get(self, brand_id: BrandId) -> Brand | None:
        model = await self._models.get(brand_id)
        return BrandMapper.to_entity(model) if model is not None else None

    @override
    async def add(self, brand: Brand) -> None:
        await self._models.add(BrandMapper.to_model(brand))

    @override
    async def save(self, brand: Brand) -> None:
        await self._models.merge(BrandMapper.to_model(brand))

    @override
    async def delete(self, brand: Brand) -> None:
        model = await self._models.get(brand.id)
        if model is not None:
            await self._models.delete(model)

    @override
    async def exists_with_title(
        self,
        title: Title,
        *,
        excluding: BrandId | None = None,
    ) -> bool:
        query = select(BrandORM.id).where(BrandORM.title == title.value)
        if excluding is not None:
            query = query.where(BrandORM.id != excluding)
        return await _exists(self._session, query)
