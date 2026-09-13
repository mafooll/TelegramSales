from datetime import datetime

import pytest

from telegramsales.modules.catalog.application.commands.products import (
    ChangeProductStock,
    ChangeProductStockHandler,
    ChangeProductVisibility,
    ChangeProductVisibilityHandler,
    CreateProduct,
    CreateProductHandler,
    DeleteProduct,
    DeleteProductHandler,
    PublishProduct,
    PublishProductHandler,
    RebrandProduct,
    RebrandProductHandler,
    RenameProduct,
    RenameProductHandler,
    RepriceProduct,
    RepriceProductHandler,
)
from telegramsales.modules.catalog.application.exceptions import (
    BrandNotFoundError,
    CatalogNotFoundError,
    ProductNotFoundError,
)
from telegramsales.modules.catalog.contracts import BrandId, CatalogId, ProductId
from telegramsales.modules.catalog.domain.entities import Product
from telegramsales.modules.catalog.domain.events import ProductPublished
from telegramsales.modules.catalog.domain.exceptions import (
    ForeignCatalogError,
    PriceNotDiscountedError,
    ProductWithoutPhotoError,
)
from telegramsales.modules.catalog.domain.permissions import CatalogPermission
from telegramsales.modules.catalog.domain.values import Description, Title
from telegramsales.shared.application.access import PermissionDeniedError
from tests.catalog.factories import (
    ACME,
    BEAUTY,
    CLOTHES,
    COAT,
    NOW,
    OUTERWEAR,
    make_brand,
    make_catalog,
    make_category,
    make_media,
    make_product,
    rub,
)
from tests.catalog.fakes import (
    FakeBrandRepository,
    FakeCatalogRepository,
    FakeCatalogUnitOfWork,
    FakeCategoryRepository,
    FakeEventPublisher,
    FakeProductMediaRepository,
    FakeProductRepository,
    FixedClock,
    actor_with,
)

MANAGER = actor_with(CatalogPermission.MANAGE)
OUTSIDER = actor_with()
MISSING = ProductId(COAT)


def uow_with(*products: Product) -> FakeCatalogUnitOfWork:
    return FakeCatalogUnitOfWork(
        catalogs=FakeCatalogRepository(
            make_catalog(CLOTHES, "Одежда"), make_catalog(BEAUTY, "Бьюти")
        ),
        categories=FakeCategoryRepository(make_category()),
        brands=FakeBrandRepository(make_brand()),
        products=FakeProductRepository(*products),
    )


def new_product() -> CreateProduct:
    return CreateProduct(
        catalog_id=CLOTHES,
        category_id=OUTERWEAR,
        title=Title("Пальто"),
        description=Description("Тёплое."),
        price=rub("12900"),
    )


async def test_created_product_gets_an_article() -> None:
    uow = uow_with()

    product_id = await CreateProductHandler(uow, FixedClock(NOW)).handle(
        new_product(), MANAGER
    )

    assert uow.products.items[product_id].article.value


async def test_created_product_is_not_published() -> None:
    uow = uow_with()

    product_id = await CreateProductHandler(uow, FixedClock(NOW)).handle(
        new_product(), MANAGER
    )

    assert not uow.products.items[product_id].is_published


async def test_articles_do_not_repeat() -> None:
    uow = uow_with()
    handler = CreateProductHandler(uow, FixedClock(NOW))

    first = await handler.handle(new_product(), MANAGER)
    second = await handler.handle(new_product(), MANAGER)

    assert uow.products.items[first].article != uow.products.items[second].article


async def test_category_from_another_catalog_is_rejected() -> None:
    uow = uow_with()
    command = CreateProduct(
        catalog_id=BEAUTY,
        category_id=OUTERWEAR,
        title=Title("Пальто"),
        description=Description("Тёплое."),
        price=rub("12900"),
    )

    with pytest.raises(ForeignCatalogError):
        await CreateProductHandler(uow, FixedClock(NOW)).handle(command, MANAGER)


async def test_missing_catalog_is_rejected() -> None:
    uow = uow_with()
    command = CreateProduct(
        catalog_id=CatalogId(404),
        category_id=OUTERWEAR,
        title=Title("Пальто"),
        description=Description("Тёплое."),
        price=rub("12900"),
    )

    with pytest.raises(CatalogNotFoundError):
        await CreateProductHandler(uow, FixedClock(NOW)).handle(command, MANAGER)


async def test_missing_brand_is_rejected() -> None:
    uow = uow_with()
    command = CreateProduct(
        catalog_id=CLOTHES,
        category_id=OUTERWEAR,
        title=Title("Пальто"),
        description=Description("Тёплое."),
        price=rub("12900"),
        brand_id=BrandId(404),
    )

    with pytest.raises(BrandNotFoundError):
        await CreateProductHandler(uow, FixedClock(NOW)).handle(command, MANAGER)


async def test_outsider_cannot_create_a_product() -> None:
    uow = uow_with()

    with pytest.raises(PermissionDeniedError):
        await CreateProductHandler(uow, FixedClock(NOW)).handle(
            new_product(), OUTSIDER
        )


async def test_product_is_renamed() -> None:
    uow = uow_with(make_product())

    await RenameProductHandler(uow).handle(
        RenameProduct(product_id=COAT, title=Title("Пальто зимнее")), MANAGER
    )

    assert uow.products.items[COAT].title == Title("Пальто зимнее")


async def test_renaming_a_missing_product_is_rejected() -> None:
    uow = uow_with()

    with pytest.raises(ProductNotFoundError):
        await RenameProductHandler(uow).handle(
            RenameProduct(product_id=MISSING, title=Title("Пальто")), MANAGER
        )


async def test_price_is_changed() -> None:
    uow = uow_with(make_product())

    await RepriceProductHandler(uow).handle(
        RepriceProduct(product_id=COAT, price=rub("9900"), old_price=rub("12900")),
        MANAGER,
    )

    assert uow.products.items[COAT].is_on_sale


async def test_a_bad_discount_is_rejected() -> None:
    uow = uow_with(make_product(price="12900"))

    with pytest.raises(PriceNotDiscountedError):
        await RepriceProductHandler(uow).handle(
            RepriceProduct(
                product_id=COAT, price=rub("12900"), old_price=rub("9900")
            ),
            MANAGER,
        )

    assert uow.rolled_back


async def test_brand_is_attached() -> None:
    uow = uow_with(make_product())

    await RebrandProductHandler(uow).handle(
        RebrandProduct(product_id=COAT, brand_id=ACME), MANAGER
    )

    assert uow.products.items[COAT].brand_id == ACME


async def test_brand_can_be_removed() -> None:
    uow = uow_with(make_product())

    await RebrandProductHandler(uow).handle(
        RebrandProduct(product_id=COAT, brand_id=None), MANAGER
    )

    assert uow.products.items[COAT].brand_id is None


def publishing(
    uow: FakeCatalogUnitOfWork,
    moment: datetime = NOW,
) -> tuple[PublishProductHandler, FakeEventPublisher]:
    events = FakeEventPublisher()
    return PublishProductHandler(uow, FixedClock(moment), events), events


def with_a_photo(product: Product) -> FakeCatalogUnitOfWork:
    return FakeCatalogUnitOfWork(
        products=FakeProductRepository(product),
        media=FakeProductMediaRepository(make_media()),
    )


async def test_a_product_without_photos_is_not_published() -> None:
    uow = uow_with(make_product())
    handler, _ = publishing(uow)

    with pytest.raises(ProductWithoutPhotoError):
        await handler.handle(PublishProduct(product_id=COAT), MANAGER)

    assert not uow.products.items[COAT].is_published


async def test_a_product_with_a_photo_is_published() -> None:
    uow = with_a_photo(make_product())
    handler, _ = publishing(uow)

    await handler.handle(PublishProduct(product_id=COAT), MANAGER)

    assert uow.products.items[COAT].published_at == NOW


async def test_the_first_publication_announces_the_product() -> None:
    uow = with_a_photo(make_product())
    handler, events = publishing(uow)

    await handler.handle(PublishProduct(product_id=COAT), MANAGER)

    assert len(events.published) == 1
    event = events.published[0]
    assert isinstance(event, ProductPublished)
    assert event.product_id == COAT
    assert event.title == uow.products.items[COAT].title.value


async def test_publishing_twice_keeps_the_first_moment() -> None:
    uow = with_a_photo(make_product(published=True))
    later = NOW.replace(year=NOW.year + 1)
    handler, _ = publishing(uow, later)

    await handler.handle(PublishProduct(product_id=COAT), MANAGER)

    assert uow.products.items[COAT].published_at == NOW


async def test_a_returned_product_is_not_announced_again() -> None:
    uow = with_a_photo(make_product(published=True))
    handler, events = publishing(uow)

    await handler.handle(PublishProduct(product_id=COAT), MANAGER)

    assert events.published == []


async def test_product_is_hidden_and_brought_back() -> None:
    uow = uow_with(make_product(published=True))
    handler = ChangeProductVisibilityHandler(uow)

    await handler.handle(
        ChangeProductVisibility(product_id=COAT, is_visible=False), MANAGER
    )
    hidden = uow.products.items[COAT].is_visible

    await handler.handle(
        ChangeProductVisibility(product_id=COAT, is_visible=True), MANAGER
    )

    assert not hidden
    assert uow.products.items[COAT].is_visible


async def test_product_runs_out_and_returns() -> None:
    uow = uow_with(make_product())
    handler = ChangeProductStockHandler(uow)

    await handler.handle(
        ChangeProductStock(product_id=COAT, is_in_stock=False), MANAGER
    )
    out = uow.products.items[COAT].is_in_stock

    await handler.handle(
        ChangeProductStock(product_id=COAT, is_in_stock=True), MANAGER
    )

    assert not out
    assert uow.products.items[COAT].is_in_stock


async def test_published_product_can_still_be_deleted() -> None:
    uow = uow_with(make_product(published=True))

    await DeleteProductHandler(uow).handle(DeleteProduct(product_id=COAT), MANAGER)

    assert COAT not in uow.products.items


async def test_outsider_cannot_delete_a_product() -> None:
    uow = uow_with(make_product())

    with pytest.raises(PermissionDeniedError):
        await DeleteProductHandler(uow).handle(
            DeleteProduct(product_id=COAT), OUTSIDER
        )

    assert COAT in uow.products.items
