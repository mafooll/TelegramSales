from decimal import Decimal
from typing import Any, override

from sqlalchemy import Select, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from telegramsales.modules.catalog.application.ports import IShopQueries
from telegramsales.modules.catalog.application.queries import (
    ShopCatalogView,
    ShopCategoryView,
    ShopProductEntryView,
    ShopProductView,
    ShopVariantView,
)
from telegramsales.modules.catalog.contracts import (
    CatalogId,
    CategoryId,
    ProductId,
    VariantId,
)
from telegramsales.modules.catalog.domain.enums import MediaKind, MediaLayout
from telegramsales.modules.catalog.infrastructure.filters import (
    category_filter,
    parent_filter,
)
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
_child_product = aliased(ProductORM)
_parent = aliased(CategoryORM)

CATALOG_TITLE = (
    select(CatalogORM.title)
    .where(CatalogORM.id == CategoryORM.catalog_id)
    .scalar_subquery()
    .label("catalog_title")
)

PARENT_TITLE = (
    select(_parent.title)
    .where(_parent.id == CategoryORM.parent_id)
    .scalar_subquery()
    .label("parent_title")
)

THUMBNAIL = (
    select(ProductMediaORM.file_id)
    .where(
        ProductMediaORM.product_id == ProductORM.id,
        ProductMediaORM.kind == MediaKind.PHOTO.value,
    )
    .order_by(ProductMediaORM.position, ProductMediaORM.id)
    .limit(1)
    .scalar_subquery()
    .label("thumbnail")
)

HAS_VARIANTS = (
    select(ProductVariantORM.id)
    .where(ProductVariantORM.product_id == ProductORM.id)
    .exists()
    .label("has_variants")
)

PRODUCT_COUNT = (
    select(func.count())
    .select_from(ProductORM)
    .where(
        ProductORM.category_id == CategoryORM.id,
        ProductORM.published_at.is_not(None),
        ProductORM.is_visible.is_(True),
    )
    .scalar_subquery()
    .label("product_count")
)

CHILD_PRODUCT_COUNT = (
    select(func.count())
    .select_from(_child_product)
    .where(
        _child_product.category_id == _child.id,
        _child_product.published_at.is_not(None),
        _child_product.is_visible.is_(True),
    )
    .scalar_subquery()
)

CHILD_COUNT = (
    select(func.count())
    .select_from(_child)
    .where(
        _child.parent_id == CategoryORM.id,
        _child.is_active.is_(True),
        CHILD_PRODUCT_COUNT > 0,
    )
    .scalar_subquery()
    .label("child_count")
)


type CategoryRow = tuple[int, int, int | None, str, str, str, int, int]


def _category_query() -> Select[CategoryRow]:
    return select(
        CategoryORM.id,
        CategoryORM.catalog_id,
        CategoryORM.parent_id,
        CategoryORM.title,
        CATALOG_TITLE,
        PARENT_TITLE,
        CHILD_COUNT,
        PRODUCT_COUNT,
    ).where(CategoryORM.is_active.is_(True))


def _stocked_query() -> Select[CategoryRow]:
    return _category_query().where(or_(CHILD_COUNT > 0, PRODUCT_COUNT > 0))


def _product_entries() -> Select[tuple[Any, str, Decimal, str, bool, str, bool]]:
    return select(
        ProductORM.id,
        ProductORM.title,
        ProductORM.price,
        ProductORM.currency,
        ProductORM.is_in_stock,
        THUMBNAIL,
        HAS_VARIANTS,
    ).where(
        ProductORM.published_at.is_not(None),
        ProductORM.is_visible.is_(True),
    )


SIMILARITY = 0.4
ARTICLE_RANK = 0
BRAND_RANK = 1
TITLE_RANK = 2


def _found_entries(needle: str) -> Select[tuple[Any, ...]]:
    lowered = needle.lower()
    brand_title = func.coalesce(BrandORM.title, "")

    by_article = func.lower(ProductORM.article).like(f"{lowered}%")
    by_brand = or_(
        func.lower(brand_title).like(f"%{lowered}%"),
        func.word_similarity(needle, brand_title) >= SIMILARITY,
    )
    by_title = or_(
        func.lower(ProductORM.title).like(f"%{lowered}%"),
        func.word_similarity(needle, ProductORM.title) >= SIMILARITY,
    )

    rank = case(
        (by_article, ARTICLE_RANK),
        (by_brand, BRAND_RANK),
        else_=TITLE_RANK,
    ).label("rank")
    score = func.greatest(
        func.word_similarity(needle, ProductORM.title),
        func.word_similarity(needle, brand_title),
    ).label("score")

    return (
        _product_entries()
        .add_columns(rank, score)
        .outerjoin(
            BrandORM,
            (ProductORM.brand_id == BrandORM.id) & BrandORM.is_active.is_(True),
        )
        .where(or_(by_article, by_brand, by_title))
        .order_by(rank, score.desc(), ProductORM.title)
    )


async def _total[RowsType: tuple[Any, ...]](
    session: AsyncSession,
    query: Select[RowsType],
) -> int:
    counted = select(func.count()).select_from(query.subquery())
    return (await session.execute(counted)).scalar_one()


def _money(amount: Decimal, currency: str) -> Money:
    return Money(amount, Currency(currency))


def _entry_view(row: Any) -> ShopProductEntryView:  # noqa: ANN401
    return ShopProductEntryView(
        id=ProductId(row.id),
        title=row.title,
        price=_money(row.price, row.currency),
        is_in_stock=row.is_in_stock,
        thumbnail=row.thumbnail,
        has_variants=row.has_variants,
    )


def _category_view(row: Any) -> ShopCategoryView:  # noqa: ANN401
    return ShopCategoryView(
        id=CategoryId(row.id),
        catalog_id=CatalogId(row.catalog_id),
        parent_id=None if row.parent_id is None else CategoryId(row.parent_id),
        title=row.title,
        catalog_title=row.catalog_title,
        parent_title=row.parent_title,
        child_count=row.child_count,
        product_count=row.product_count,
    )


class ShopQueries(IShopQueries):
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session

    @override
    async def list_catalogs(self, number: int, size: int) -> Page[ShopCatalogView]:
        query = (
            select(CatalogORM.id, CatalogORM.title)
            .where(CatalogORM.is_active.is_(True))
            .order_by(CatalogORM.sort_order, CatalogORM.title)
        )
        total = await _total(self._session, query)
        rows = (
            await self._session.execute(query.limit(size).offset(number * size))
        ).all()

        return Page(
            items=[
                ShopCatalogView(id=CatalogId(row.id), title=row.title)
                for row in rows
            ],
            number=number,
            size=size,
            total=total,
        )

    @override
    async def get_catalog(self, catalog_id: CatalogId) -> ShopCatalogView | None:
        query = select(CatalogORM.id, CatalogORM.title).where(
            CatalogORM.id == catalog_id,
            CatalogORM.is_active.is_(True),
        )
        row = (await self._session.execute(query)).one_or_none()
        if row is None:
            return None
        return ShopCatalogView(id=CatalogId(row.id), title=row.title)

    @override
    async def get_category(self, category_id: CategoryId) -> ShopCategoryView | None:
        query = _category_query().where(CategoryORM.id == category_id)
        row = (await self._session.execute(query)).one_or_none()
        if row is None:
            return None
        return _category_view(row)

    @override
    async def list_categories(
        self,
        catalog_id: CatalogId,
        parent_id: CategoryId | None,
        number: int,
        size: int,
    ) -> Page[ShopCategoryView]:
        query = (
            _stocked_query()
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
            items=[_category_view(row) for row in rows],
            number=number,
            size=size,
            total=total,
        )

    @override
    async def list_products(
        self,
        catalog_id: CatalogId,
        category_id: CategoryId | None,
        number: int,
        size: int,
    ) -> Page[ShopProductEntryView]:
        query = (
            _product_entries()
            .where(
                ProductORM.catalog_id == catalog_id,
                category_filter(category_id),
            )
            .order_by(ProductORM.created_at.desc(), ProductORM.title)
        )
        total = await _total(self._session, query)
        rows = (
            await self._session.execute(query.limit(size).offset(number * size))
        ).all()

        return Page(
            items=[_entry_view(row) for row in rows],
            number=number,
            size=size,
            total=total,
        )

    @override
    async def search_products(
        self,
        needle: str,
        number: int,
        size: int,
    ) -> Page[ShopProductEntryView]:
        query = _found_entries(needle)
        total = await _total(self._session, query)
        rows = (
            await self._session.execute(query.limit(size).offset(number * size))
        ).all()

        return Page(
            items=[_entry_view(row) for row in rows],
            number=number,
            size=size,
            total=total,
        )

    @override
    async def get_product(self, product_id: ProductId) -> ShopProductView | None:
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
                ProductORM.media_layout,
                ProductORM.is_in_stock,
                BrandORM.title.label("brand_title"),
            )
            .outerjoin(
                BrandORM,
                (ProductORM.brand_id == BrandORM.id) & BrandORM.is_active.is_(True),
            )
            .where(
                ProductORM.id == product_id,
                ProductORM.published_at.is_not(None),
                ProductORM.is_visible.is_(True),
            )
        )
        row = (await self._session.execute(query)).one_or_none()
        if row is None:
            return None

        photos, clip = await self._media(ProductId(row.id))
        return ShopProductView(
            id=ProductId(row.id),
            catalog_id=CatalogId(row.catalog_id),
            category_id=(
                None if row.category_id is None else CategoryId(row.category_id)
            ),
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
            is_in_stock=row.is_in_stock,
            photo_ids=photos,
            video_id=clip,
            media_layout=MediaLayout(row.media_layout),
            variants=await self._variants(ProductId(row.id), row.currency),
        )

    async def _media(
        self,
        product_id: ProductId,
    ) -> tuple[tuple[str, ...], str | None]:
        query = (
            select(ProductMediaORM.kind, ProductMediaORM.file_id)
            .where(ProductMediaORM.product_id == product_id)
            .order_by(ProductMediaORM.position, ProductMediaORM.id)
        )
        rows = (await self._session.execute(query)).all()
        photos = tuple(
            row.file_id for row in rows if row.kind == MediaKind.PHOTO.value
        )
        clip = next(
            (row.file_id for row in rows if row.kind == MediaKind.VIDEO.value), None
        )
        return photos, clip

    async def _variants(
        self,
        product_id: ProductId,
        currency: str,
    ) -> tuple[ShopVariantView, ...]:
        query = (
            select(
                ProductVariantORM.id,
                ProductVariantORM.title,
                func.coalesce(
                    ProductVariantORM.price_override, ProductORM.price
                ).label("price"),
            )
            .join(ProductORM, ProductVariantORM.product_id == ProductORM.id)
            .where(
                ProductVariantORM.product_id == product_id,
                ProductVariantORM.is_available.is_(True),
            )
            .order_by(ProductVariantORM.position, ProductVariantORM.title)
        )
        rows = (await self._session.execute(query)).all()
        return tuple(
            ShopVariantView(
                id=VariantId(row.id),
                title=row.title,
                price=_money(row.price, currency),
            )
            for row in rows
        )
