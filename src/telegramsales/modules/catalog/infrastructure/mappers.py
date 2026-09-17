from typing import override

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
from telegramsales.modules.catalog.domain.enums import MediaKind, MediaLayout
from telegramsales.modules.catalog.domain.values import Article, Description, Title
from telegramsales.modules.catalog.infrastructure.models import (
    BrandORM,
    CatalogORM,
    CategoryORM,
    ProductMediaORM,
    ProductORM,
    ProductVariantORM,
)
from telegramsales.shared.domain.money import Currency, Money
from telegramsales.shared.infrastructure.database.mapper import IEntityMapper

DEFAULT_CURRENCY = Currency.USD


class CatalogMapper(IEntityMapper[Catalog, CatalogORM]):
    @staticmethod
    @override
    def to_entity(model: CatalogORM) -> Catalog:
        return Catalog(
            id=CatalogId(model.id),
            title=Title(model.title),
            created_at=model.created_at,
            sort_order=model.sort_order,
            is_active=model.is_active,
        )

    @staticmethod
    @override
    def to_model(entity: Catalog) -> CatalogORM:
        return CatalogORM(
            id=entity.id,
            title=entity.title.value,
            created_at=entity.created_at,
            sort_order=entity.sort_order,
            is_active=entity.is_active,
        )


class CategoryMapper(IEntityMapper[Category, CategoryORM]):
    @staticmethod
    @override
    def to_entity(model: CategoryORM) -> Category:
        return Category(
            id=CategoryId(model.id),
            catalog_id=CatalogId(model.catalog_id),
            parent_id=None
            if model.parent_id is None
            else CategoryId(model.parent_id),
            title=Title(model.title),
            created_at=model.created_at,
            sort_order=model.sort_order,
            is_active=model.is_active,
        )

    @staticmethod
    @override
    def to_model(entity: Category) -> CategoryORM:
        return CategoryORM(
            id=entity.id,
            catalog_id=entity.catalog_id,
            parent_id=entity.parent_id,
            title=entity.title.value,
            created_at=entity.created_at,
            sort_order=entity.sort_order,
            is_active=entity.is_active,
        )


class BrandMapper(IEntityMapper[Brand, BrandORM]):
    @staticmethod
    @override
    def to_entity(model: BrandORM) -> Brand:
        return Brand(
            id=BrandId(model.id),
            title=Title(model.title),
            created_at=model.created_at,
            sort_order=model.sort_order,
            is_active=model.is_active,
        )

    @staticmethod
    @override
    def to_model(entity: Brand) -> BrandORM:
        return BrandORM(
            id=entity.id,
            title=entity.title.value,
            created_at=entity.created_at,
            sort_order=entity.sort_order,
            is_active=entity.is_active,
        )


class ProductMapper(IEntityMapper[Product, ProductORM]):
    @staticmethod
    @override
    def to_entity(model: ProductORM) -> Product:
        currency = Currency(model.currency)
        return Product(
            id=ProductId(model.id),
            catalog_id=CatalogId(model.catalog_id),
            category_id=(
                None if model.category_id is None else CategoryId(model.category_id)
            ),
            brand_id=None if model.brand_id is None else BrandId(model.brand_id),
            article=Article(model.article),
            title=Title(model.title),
            description=Description(model.description),
            price=Money(model.price, currency),
            old_price=(
                None if model.old_price is None else Money(model.old_price, currency)
            ),
            variant_label=(
                None if model.variant_label is None else Title(model.variant_label)
            ),
            media_layout=MediaLayout(model.media_layout),
            published_at=model.published_at,
            is_visible=model.is_visible,
            is_in_stock=model.is_in_stock,
            created_at=model.created_at,
        )

    @staticmethod
    @override
    def to_model(entity: Product) -> ProductORM:
        return ProductORM(
            id=entity.id,
            catalog_id=entity.catalog_id,
            category_id=entity.category_id,
            brand_id=entity.brand_id,
            article=entity.article.value,
            title=entity.title.value,
            description=entity.description.value,
            price=entity.price.amount,
            old_price=None if entity.old_price is None else entity.old_price.amount,
            currency=entity.price.currency.value,
            variant_label=(
                None if entity.variant_label is None else entity.variant_label.value
            ),
            media_layout=entity.media_layout.value,
            published_at=entity.published_at,
            is_visible=entity.is_visible,
            is_in_stock=entity.is_in_stock,
            created_at=entity.created_at,
        )


class ProductVariantMapper(IEntityMapper[ProductVariant, ProductVariantORM]):
    @staticmethod
    @override
    def to_entity(model: ProductVariantORM) -> ProductVariant:
        return ProductVariant(
            id=VariantId(model.id),
            product_id=ProductId(model.product_id),
            title=Title(model.title),
            price_override=(
                None
                if model.price_override is None
                else Money(model.price_override, Currency(model.currency))
            ),
            position=model.position,
            is_available=model.is_available,
        )

    @staticmethod
    @override
    def to_model(entity: ProductVariant) -> ProductVariantORM:
        override_price = entity.price_override
        return ProductVariantORM(
            id=entity.id,
            product_id=entity.product_id,
            title=entity.title.value,
            price_override=None if override_price is None else override_price.amount,
            currency=(
                DEFAULT_CURRENCY.value
                if override_price is None
                else override_price.currency.value
            ),
            position=entity.position,
            is_available=entity.is_available,
        )


class ProductMediaMapper(IEntityMapper[ProductMedia, ProductMediaORM]):
    @staticmethod
    @override
    def to_entity(model: ProductMediaORM) -> ProductMedia:
        return ProductMedia(
            id=MediaId(model.id),
            product_id=ProductId(model.product_id),
            kind=MediaKind(model.kind),
            file_id=model.file_id,
            position=model.position,
        )

    @staticmethod
    @override
    def to_model(entity: ProductMedia) -> ProductMediaORM:
        return ProductMediaORM(
            id=entity.id,
            product_id=entity.product_id,
            kind=entity.kind.value,
            file_id=entity.file_id,
            position=entity.position,
        )
