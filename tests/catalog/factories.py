from datetime import UTC, datetime

from telegramsales.modules.catalog.contracts import (
    BrandId,
    CatalogId,
    CategoryId,
)
from telegramsales.modules.catalog.domain.entities import Brand, Catalog, Category
from telegramsales.modules.catalog.domain.values import Title

NOW = datetime(2026, 9, 11, 12, 0, tzinfo=UTC)

CLOTHES = CatalogId(1)
BEAUTY = CatalogId(2)

OUTERWEAR = CategoryId(10)
COATS = CategoryId(11)
SKINCARE = CategoryId(20)

ACME = BrandId(100)


def make_catalog(
    catalog_id: CatalogId = CLOTHES,
    title: str = "Одежда",
) -> Catalog:
    return Catalog.create(
        catalog_id=catalog_id,
        title=Title(title),
        now=NOW,
    )


def make_category(
    category_id: CategoryId = OUTERWEAR,
    title: str = "Верхняя одежда",
    *,
    catalog_id: CatalogId = CLOTHES,
    parent_id: CategoryId | None = None,
) -> Category:
    return Category.create(
        category_id=category_id,
        catalog_id=catalog_id,
        title=Title(title),
        now=NOW,
        parent_id=parent_id,
    )


def make_brand(brand_id: BrandId = ACME, title: str = "Acme") -> Brand:
    return Brand.create(brand_id=brand_id, title=Title(title), now=NOW)
