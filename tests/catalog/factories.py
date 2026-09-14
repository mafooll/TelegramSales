from datetime import UTC, datetime
from uuid import UUID

from telegramsales.modules.catalog.contracts import (
    BrandId,
    CatalogId,
    CategoryId,
    MediaId,
    ProductId,
    VariantId,
)
from telegramsales.modules.catalog.domain.entities import (
    DEFAULT_SORT_ORDER,
    Brand,
    Catalog,
    Category,
    Product,
    ProductMedia,
    ProductVariant,
)
from telegramsales.modules.catalog.domain.enums import MediaKind
from telegramsales.modules.catalog.domain.values import Article, Description, Title
from telegramsales.shared.domain.money import Currency, Money

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


COAT = ProductId(UUID("11111111-1111-1111-1111-111111111111"))
DRESS = ProductId(UUID("22222222-2222-2222-2222-222222222222"))
SIZE_M = VariantId(500)
FRONT_PHOTO = MediaId(600)


def rub(amount: str) -> Money:
    return Money.from_external(amount, Currency.RUB)


def make_product(
    product_id: ProductId = COAT,
    title: str = "Пальто оверсайз",
    *,
    price: str = "12900",
    variant_label: str | None = None,
    published: bool = False,
) -> Product:
    product = Product.create(
        product_id=product_id,
        catalog_id=CLOTHES,
        category_id=OUTERWEAR,
        title=Title(title),
        description=Description("Тёплое пальто из шерсти."),
        article=Article.of(42),
        price=rub(price),
        now=NOW,
        brand_id=ACME,
    )
    if variant_label is not None:
        product.open_variants(Title(variant_label))
    if published:
        product.publish(NOW)
        product.collect_events()
    return product


def make_variant(
    variant_id: VariantId = SIZE_M,
    title: str = "M",
    *,
    product_id: ProductId = COAT,
    price_override: str | None = None,
) -> ProductVariant:
    return ProductVariant.create(
        variant_id=variant_id,
        product_id=product_id,
        title=Title(title),
        price_override=None if price_override is None else rub(price_override),
    )


def make_media(
    media_id: MediaId = FRONT_PHOTO,
    kind: MediaKind = MediaKind.PHOTO,
    *,
    product_id: ProductId = COAT,
    file_id: str = "file-front",
    position: int = DEFAULT_SORT_ORDER,
) -> ProductMedia:
    return ProductMedia.create(
        media_id=media_id,
        product_id=product_id,
        kind=kind,
        file_id=file_id,
        position=position,
    )
