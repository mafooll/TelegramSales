from decimal import Decimal
from typing import Any, override

from sqlalchemy import Label, Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from telegramsales.modules.catalog.application.ports import (
    ICatalogQueries,
    IProductQueries,
)
from telegramsales.modules.catalog.application.queries import (
    BrandView,
    CatalogView,
    CategoryView,
    MediaView,
    ProductEntryView,
    ProductView,
    VariantView,
)
from telegramsales.modules.catalog.contracts import (
    BrandId,
    CatalogId,
    CategoryId,
    MediaId,
    ProductId,
    VariantId,
)
from telegramsales.modules.catalog.domain.enums import MediaKind
from telegramsales.modules.catalog.infrastructure.filters import parent_filter
from telegramsales.modules.catalog.infrastructure.models import (
    BrandORM,
    CatalogORM,
    CategoryORM,
    ProductMediaORM,
    ProductORM,
    ProductVariantORM,
)
from telegramsales.shared.application.pagination import Page
from telegramsales.shared.domain.money import Currency, Money

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


def _media_count(kind: MediaKind, label: str) -> Label[int]:
    return (
        select(func.count())
        .select_from(ProductMediaORM)
        .where(
            ProductMediaORM.product_id == ProductORM.id,
            ProductMediaORM.kind == kind.value,
        )
        .scalar_subquery()
        .label(label)
    )


PHOTO_COUNT = _media_count(MediaKind.PHOTO, "photo_count")
VIDEO_COUNT = _media_count(MediaKind.VIDEO, "video_count")

VARIANT_COUNT = (
    select(func.count())
    .select_from(ProductVariantORM)
    .where(ProductVariantORM.product_id == ProductORM.id)
    .scalar_subquery()
    .label("variant_count")
)


def _money(amount: Decimal, currency: str) -> Money:
    return Money(amount, Currency(currency))


class ProductQueries(IProductQueries):
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session

    @override
    async def get_product(self, product_id: ProductId) -> ProductView | None:
        query = (
            select(
                ProductORM.id,
                ProductORM.catalog_id,
                ProductORM.category_id,
                ProductORM.article,
                ProductORM.title,
                ProductORM.description,
                ProductORM.price,
                ProductORM.old_price,
                ProductORM.currency,
                ProductORM.variant_label,
                ProductORM.published_at,
                ProductORM.is_visible,
                ProductORM.is_in_stock,
                BrandORM.title.label("brand_title"),
                PHOTO_COUNT,
                VIDEO_COUNT,
                VARIANT_COUNT,
            )
            .outerjoin(BrandORM, ProductORM.brand_id == BrandORM.id)
            .where(ProductORM.id == product_id)
        )
        row = (await self._session.execute(query)).one_or_none()
        if row is None:
            return None

        return ProductView(
            id=ProductId(row.id),
            catalog_id=CatalogId(row.catalog_id),
            category_id=CategoryId(row.category_id),
            article=row.article,
            title=row.title,
            description=row.description,
            price=_money(row.price, row.currency),
            old_price=(
                None
                if row.old_price is None
                else _money(row.old_price, row.currency)
            ),
            brand_title=row.brand_title,
            variant_label=row.variant_label,
            is_published=row.published_at is not None,
            is_visible=row.is_visible,
            is_in_stock=row.is_in_stock,
            photo_count=row.photo_count,
            video_count=row.video_count,
            variant_count=row.variant_count,
        )

    @override
    async def list_products(
        self,
        category_id: CategoryId,
        number: int,
        size: int,
    ) -> Page[ProductEntryView]:
        query = (
            select(
                ProductORM.id,
                ProductORM.title,
                ProductORM.price,
                ProductORM.currency,
                ProductORM.published_at,
                ProductORM.is_visible,
                ProductORM.is_in_stock,
            )
            .where(ProductORM.category_id == category_id)
            .order_by(ProductORM.created_at, ProductORM.title)
        )
        total = await _total(self._session, query)
        rows = (
            await self._session.execute(query.limit(size).offset(number * size))
        ).all()

        return Page(
            items=[
                ProductEntryView(
                    id=ProductId(row.id),
                    title=row.title,
                    price=_money(row.price, row.currency),
                    is_published=row.published_at is not None,
                    is_visible=row.is_visible,
                    is_in_stock=row.is_in_stock,
                )
                for row in rows
            ],
            number=number,
            size=size,
            total=total,
        )

    @override
    async def list_variants(self, product_id: ProductId) -> list[VariantView]:
        query = (
            select(
                ProductVariantORM.id,
                ProductVariantORM.title,
                func.coalesce(
                    ProductVariantORM.price_override, ProductORM.price
                ).label("price"),
                ProductORM.currency,
                ProductVariantORM.is_available,
            )
            .join(ProductORM, ProductVariantORM.product_id == ProductORM.id)
            .where(ProductVariantORM.product_id == product_id)
            .order_by(ProductVariantORM.position, ProductVariantORM.title)
        )
        rows = (await self._session.execute(query)).all()

        return [
            VariantView(
                id=VariantId(row.id),
                title=row.title,
                price=_money(row.price, row.currency),
                is_available=row.is_available,
            )
            for row in rows
        ]

    @override
    async def list_media(self, product_id: ProductId) -> list[MediaView]:
        query = (
            select(
                ProductMediaORM.id,
                ProductMediaORM.kind,
                ProductMediaORM.file_id,
            )
            .where(ProductMediaORM.product_id == product_id)
            .order_by(ProductMediaORM.position, ProductMediaORM.id)
        )
        rows = (await self._session.execute(query)).all()

        return [
            MediaView(
                id=MediaId(row.id),
                kind=MediaKind(row.kind),
                file_id=row.file_id,
            )
            for row in rows
        ]
