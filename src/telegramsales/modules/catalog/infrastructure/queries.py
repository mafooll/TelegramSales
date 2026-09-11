from typing import Any, override

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from telegramsales.modules.catalog.application.ports import ICatalogQueries
from telegramsales.modules.catalog.application.queries import (
    BrandView,
    CatalogView,
    CategoryView,
)
from telegramsales.modules.catalog.contracts import (
    BrandId,
    CatalogId,
    CategoryId,
)
from telegramsales.modules.catalog.infrastructure.filters import parent_filter
from telegramsales.modules.catalog.infrastructure.models import (
    BrandORM,
    CatalogORM,
    CategoryORM,
)
from telegramsales.shared.application.pagination import Page

_child = aliased(CategoryORM)

CATEGORY_COUNT = (
    select(func.count())
    .select_from(CategoryORM)
    .where(CategoryORM.catalog_id == CatalogORM.id)
    .scalar_subquery()
    .label("category_count")
)

CHILD_COUNT = (
    select(func.count())
    .select_from(_child)
    .where(_child.parent_id == CategoryORM.id)
    .scalar_subquery()
    .label("child_count")
)


def _catalog_query() -> Select[tuple[int, str, bool, int]]:
    return select(
        CatalogORM.id,
        CatalogORM.title,
        CatalogORM.is_active,
        CATEGORY_COUNT,
    )


def _category_query() -> Select[tuple[int, int, int | None, str, bool, int]]:
    return select(
        CategoryORM.id,
        CategoryORM.catalog_id,
        CategoryORM.parent_id,
        CategoryORM.title,
        CategoryORM.is_active,
        CHILD_COUNT,
    )


def _brand_query() -> Select[tuple[int, str, bool]]:
    return select(BrandORM.id, BrandORM.title, BrandORM.is_active)


async def _total[RowsType: tuple[Any, ...]](
    session: AsyncSession,
    query: Select[RowsType],
) -> int:
    counted = select(func.count()).select_from(query.subquery())
    return (await session.execute(counted)).scalar_one()


class CatalogQueries(ICatalogQueries):
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session

    @override
    async def get_catalog(self, catalog_id: CatalogId) -> CatalogView | None:
        query = _catalog_query().where(CatalogORM.id == catalog_id)
        row = (await self._session.execute(query)).one_or_none()
        if row is None:
            return None
        return CatalogView(
            id=CatalogId(row.id),
            title=row.title,
            is_active=row.is_active,
            category_count=row.category_count,
        )

    @override
    async def list_catalogs(self, number: int, size: int) -> Page[CatalogView]:
        query = _catalog_query().order_by(CatalogORM.sort_order, CatalogORM.title)
        total = await _total(self._session, query)
        rows = (
            await self._session.execute(query.limit(size).offset(number * size))
        ).all()

        return Page(
            items=[
                CatalogView(
                    id=CatalogId(row.id),
                    title=row.title,
                    is_active=row.is_active,
                    category_count=row.category_count,
                )
                for row in rows
            ],
            number=number,
            size=size,
            total=total,
        )

    @override
    async def get_category(self, category_id: CategoryId) -> CategoryView | None:
        query = _category_query().where(CategoryORM.id == category_id)
        row = (await self._session.execute(query)).one_or_none()
        if row is None:
            return None
        return CategoryView(
            id=CategoryId(row.id),
            catalog_id=CatalogId(row.catalog_id),
            parent_id=None if row.parent_id is None else CategoryId(row.parent_id),
            title=row.title,
            is_active=row.is_active,
            child_count=row.child_count,
        )

    @override
    async def list_categories(
        self,
        catalog_id: CatalogId,
        parent_id: CategoryId | None,
        number: int,
        size: int,
    ) -> Page[CategoryView]:
        query = (
            _category_query()
            .where(
                CategoryORM.catalog_id == catalog_id,
                parent_filter(parent_id),
            )
            .order_by(CategoryORM.sort_order, CategoryORM.title)
        )
        total = await _total(self._session, query)
        rows = (
            await self._session.execute(query.limit(size).offset(number * size))
        ).all()

        return Page(
            items=[
                CategoryView(
                    id=CategoryId(row.id),
                    catalog_id=CatalogId(row.catalog_id),
                    parent_id=(
                        None if row.parent_id is None else CategoryId(row.parent_id)
                    ),
                    title=row.title,
                    is_active=row.is_active,
                    child_count=row.child_count,
                )
                for row in rows
            ],
            number=number,
            size=size,
            total=total,
        )

    @override
    async def get_brand(self, brand_id: BrandId) -> BrandView | None:
        query = _brand_query().where(BrandORM.id == brand_id)
        row = (await self._session.execute(query)).one_or_none()
        if row is None:
            return None
        return BrandView(
            id=BrandId(row.id), title=row.title, is_active=row.is_active
        )

    @override
    async def list_brands(self, number: int, size: int) -> Page[BrandView]:
        query = _brand_query().order_by(BrandORM.sort_order, BrandORM.title)
        total = await _total(self._session, query)
        rows = (
            await self._session.execute(query.limit(size).offset(number * size))
        ).all()

        return Page(
            items=[
                BrandView(
                    id=BrandId(row.id),
                    title=row.title,
                    is_active=row.is_active,
                )
                for row in rows
            ],
            number=number,
            size=size,
            total=total,
        )
