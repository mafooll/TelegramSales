from typing import override
from uuid import UUID, uuid4

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from telegramsales.modules.catalog.application.ports import (
    IBrandRepository,
    ICatalogRepository,
    ICategoryRepository,
    IProductMediaRepository,
    IProductRepository,
    IProductVariantRepository,
)
from telegramsales.modules.catalog.contracts import (
    BrandId,
    CatalogId,
    CategoryId,
    MediaId,
    ProductId,
    VariantId,
)
from telegramsales.modules.catalog.domain.entities import (
    Brand,
    Catalog,
    Category,
    Product,
    ProductMedia,
    ProductVariant,
)
from telegramsales.modules.catalog.domain.enums import MediaKind
from telegramsales.modules.catalog.domain.values import Article, Title
from telegramsales.modules.catalog.infrastructure.filters import parent_filter
from telegramsales.modules.catalog.infrastructure.mappers import (
    BrandMapper,
    CatalogMapper,
    CategoryMapper,
    ProductMapper,
    ProductMediaMapper,
    ProductVariantMapper,
)
from telegramsales.modules.catalog.infrastructure.models import (
    ARTICLE_SEQUENCE,
    BrandORM,
    CatalogORM,
    CategoryORM,
    ProductMediaORM,
    ProductORM,
    ProductVariantORM,
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


class ProductRepository(IProductRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session
        self._models: Repository[ProductORM, UUID] = Repository(session, ProductORM)

    @override
    async def next_id(self) -> ProductId:
        return ProductId(uuid4())

    @override
    async def next_article(self) -> Article:
        query = select(ARTICLE_SEQUENCE.next_value())
        return Article.of((await self._session.execute(query)).scalar_one())

    @override
    async def get(self, product_id: ProductId) -> Product | None:
        model = await self._models.get(product_id)
        return ProductMapper.to_entity(model) if model is not None else None

    @override
    async def add(self, product: Product) -> None:
        await self._models.add(ProductMapper.to_model(product))

    @override
    async def save(self, product: Product) -> None:
        await self._models.merge(ProductMapper.to_model(product))

    @override
    async def delete(self, product: Product) -> None:
        model = await self._models.get(product.id)
        if model is not None:
            await self._models.delete(model)

    @override
    async def count_in_category(self, category_id: CategoryId) -> int:
        query = (
            select(func.count())
            .select_from(ProductORM)
            .where(ProductORM.category_id == category_id)
        )
        return (await self._session.execute(query)).scalar_one()

    @override
    async def count_uncategorized(self, catalog_id: CatalogId) -> int:
        query = (
            select(func.count())
            .select_from(ProductORM)
            .where(
                ProductORM.catalog_id == catalog_id,
                ProductORM.category_id.is_(None),
            )
        )
        return (await self._session.execute(query)).scalar_one()

    @override
    async def count_of_brand(self, brand_id: BrandId) -> int:
        query = (
            select(func.count())
            .select_from(ProductORM)
            .where(ProductORM.brand_id == brand_id)
        )
        return (await self._session.execute(query)).scalar_one()


class ProductVariantRepository(IProductVariantRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session
        self._models: Repository[ProductVariantORM, int] = Repository(
            session, ProductVariantORM
        )

    @override
    async def next_id(self) -> VariantId:
        return VariantId(
            await _next_id(self._session, ProductVariantORM.__tablename__)
        )

    @override
    async def get(self, variant_id: VariantId) -> ProductVariant | None:
        model = await self._models.get(variant_id)
        return ProductVariantMapper.to_entity(model) if model is not None else None

    @override
    async def add(self, variant: ProductVariant) -> None:
        await self._models.add(ProductVariantMapper.to_model(variant))

    @override
    async def save(self, variant: ProductVariant) -> None:
        await self._models.merge(ProductVariantMapper.to_model(variant))

    @override
    async def delete(self, variant: ProductVariant) -> None:
        model = await self._models.get(variant.id)
        if model is not None:
            await self._models.delete(model)

    @override
    async def count_for(self, product_id: ProductId) -> int:
        query = (
            select(func.count())
            .select_from(ProductVariantORM)
            .where(ProductVariantORM.product_id == product_id)
        )
        return (await self._session.execute(query)).scalar_one()

    @override
    async def exists_with_title(
        self,
        title: Title,
        *,
        product_id: ProductId,
        excluding: VariantId | None = None,
    ) -> bool:
        query = select(ProductVariantORM.id).where(
            ProductVariantORM.product_id == product_id,
            ProductVariantORM.title == title.value,
        )
        if excluding is not None:
            query = query.where(ProductVariantORM.id != excluding)
        return await _exists(self._session, query)


class ProductMediaRepository(IProductMediaRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session
        self._models: Repository[ProductMediaORM, int] = Repository(
            session, ProductMediaORM
        )

    @override
    async def next_id(self) -> MediaId:
        return MediaId(await _next_id(self._session, ProductMediaORM.__tablename__))

    @override
    async def get(self, media_id: MediaId) -> ProductMedia | None:
        model = await self._models.get(media_id)
        return ProductMediaMapper.to_entity(model) if model is not None else None

    @override
    async def add(self, media: ProductMedia) -> None:
        await self._models.add(ProductMediaMapper.to_model(media))

    @override
    async def delete(self, media: ProductMedia) -> None:
        model = await self._models.get(media.id)
        if model is not None:
            await self._models.delete(model)

    @override
    async def count_of_kind(self, product_id: ProductId, kind: MediaKind) -> int:
        query = (
            select(func.count())
            .select_from(ProductMediaORM)
            .where(
                ProductMediaORM.product_id == product_id,
                ProductMediaORM.kind == kind.value,
            )
        )
        return (await self._session.execute(query)).scalar_one()

    @override
    async def first_photo(self, product_id: ProductId) -> str | None:
        query = (
            select(ProductMediaORM.file_id)
            .where(
                ProductMediaORM.product_id == product_id,
                ProductMediaORM.kind == MediaKind.PHOTO.value,
            )
            .order_by(ProductMediaORM.position, ProductMediaORM.id)
            .limit(1)
        )
        return (await self._session.execute(query)).scalar_one_or_none()
