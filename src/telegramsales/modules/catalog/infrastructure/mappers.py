from typing import override

from telegramsales.modules.catalog.contracts import (
    BrandId,
    CatalogId,
    CategoryId,
)
from telegramsales.modules.catalog.domain.entities import Brand, Catalog, Category
from telegramsales.modules.catalog.domain.values import Title
from telegramsales.modules.catalog.infrastructure.models import (
    BrandORM,
    CatalogORM,
    CategoryORM,
)
from telegramsales.shared.infrastructure.database.mapper import IEntityMapper


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
