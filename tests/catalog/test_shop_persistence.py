import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from telegramsales.modules.catalog.contracts import (
    BrandId,
    CatalogId,
    CategoryId,
)
from telegramsales.modules.catalog.domain.entities import Brand, Product
from telegramsales.modules.catalog.domain.enums import MediaKind
from telegramsales.modules.catalog.domain.values import Description, Title
from telegramsales.modules.catalog.infrastructure.repositories import (
    BrandRepository,
    CatalogRepository,
    CategoryRepository,
    ProductMediaRepository,
    ProductRepository,
    ProductVariantRepository,
)
from telegramsales.modules.catalog.infrastructure.shop_queries import ShopQueries
from tests.catalog.factories import NOW, make_media, make_variant, rub
from tests.catalog.test_persistence import make_catalog, make_category

pytestmark = pytest.mark.db

PAGE_SIZE = 8


async def make_product(  # noqa: PLR0913
    session: AsyncSession,
    catalog_id: CatalogId,
    category_id: CategoryId,
    title: str = "Пальто оверсайз",
    *,
    published: bool = True,
    brand_id: BrandId | None = None,
) -> Product:
    repository = ProductRepository(session)
    product = Product.create(
        product_id=await repository.next_id(),
        catalog_id=catalog_id,
        category_id=category_id,
        title=Title(title),
        description=Description("Тёплое пальто из шерсти."),
        article=await repository.next_article(),
        price=rub("12900"),
        now=NOW,
        brand_id=brand_id,
    )
    if published:
        product.publish(NOW)
    await repository.add(product)
    return product


async def make_brand(session: AsyncSession, title: str = "Acme") -> Brand:
    repository = BrandRepository(session)
    brand = Brand.create(
        brand_id=await repository.next_id(),
        title=Title(title),
        now=NOW,
    )
    await repository.add(brand)
    return brand


async def test_a_hidden_catalog_stays_out_of_the_shop(
    session: AsyncSession,
) -> None:
    catalog = await make_catalog(session, "Скрытый каталог")
    catalog.archive()
    await CatalogRepository(session).save(catalog)

    page = await ShopQueries(session).list_catalogs(0, PAGE_SIZE)

    assert catalog.id not in [item.id for item in page.items]


async def test_a_hidden_catalog_cannot_be_opened(session: AsyncSession) -> None:
    catalog = await make_catalog(session, "Скрытый каталог")
    catalog.archive()
    await CatalogRepository(session).save(catalog)

    assert await ShopQueries(session).get_catalog(catalog.id) is None


async def test_an_empty_category_stays_out_of_the_shop(
    session: AsyncSession,
) -> None:
    catalog = await make_catalog(session, "Каталог без товаров")
    await make_category(session, catalog.id, "Пустая категория")
    await session.flush()

    page = await ShopQueries(session).list_categories(catalog.id, None, 0, PAGE_SIZE)

    assert page.items == []


async def test_a_category_with_a_product_is_offered(session: AsyncSession) -> None:
    catalog = await make_catalog(session, "Каталог с товаром")
    category = await make_category(session, catalog.id, "Верхняя одежда")
    await make_product(session, catalog.id, category.id)
    await session.flush()

    page = await ShopQueries(session).list_categories(catalog.id, None, 0, PAGE_SIZE)

    assert [(item.id, item.product_count) for item in page.items] == [
        (category.id, 1)
    ]


async def test_a_hidden_category_stays_out_of_the_shop(
    session: AsyncSession,
) -> None:
    catalog = await make_catalog(session, "Каталог со скрытой категорией")
    category = await make_category(session, catalog.id, "Скрытая категория")
    await make_product(session, catalog.id, category.id)
    category.archive()
    await CategoryRepository(session).save(category)

    page = await ShopQueries(session).list_categories(catalog.id, None, 0, PAGE_SIZE)

    assert page.items == []


async def test_a_parent_is_offered_for_the_sake_of_its_children(
    session: AsyncSession,
) -> None:
    catalog = await make_catalog(session, "Каталог с деревом")
    parent = await make_category(session, catalog.id, "Верхняя одежда")
    child = await make_category(session, catalog.id, "Пальто", parent.id)
    await make_product(session, catalog.id, child.id)
    await session.flush()

    page = await ShopQueries(session).list_categories(catalog.id, None, 0, PAGE_SIZE)

    assert [(item.id, item.child_count) for item in page.items] == [(parent.id, 1)]


async def test_an_empty_child_does_not_keep_its_parent_alive(
    session: AsyncSession,
) -> None:
    catalog = await make_catalog(session, "Каталог с пустым деревом")
    parent = await make_category(session, catalog.id, "Верхняя одежда")
    await make_category(session, catalog.id, "Пальто", parent.id)
    await session.flush()

    page = await ShopQueries(session).list_categories(catalog.id, None, 0, PAGE_SIZE)

    assert page.items == []


async def test_an_unpublished_product_is_not_offered(
    session: AsyncSession,
) -> None:
    catalog = await make_catalog(session, "Каталог с черновиком")
    category = await make_category(session, catalog.id, "Верхняя одежда")
    await make_product(session, catalog.id, category.id, published=False)
    await session.flush()

    page = await ShopQueries(session).list_products(category.id, 0, PAGE_SIZE)

    assert page.items == []


async def test_a_hidden_product_is_not_offered(session: AsyncSession) -> None:
    catalog = await make_catalog(session, "Каталог со скрытым товаром")
    category = await make_category(session, catalog.id, "Верхняя одежда")
    product = await make_product(session, catalog.id, category.id)
    product.hide()
    await ProductRepository(session).save(product)

    page = await ShopQueries(session).list_products(category.id, 0, PAGE_SIZE)

    assert page.items == []


async def test_an_out_of_stock_product_is_still_offered(
    session: AsyncSession,
) -> None:
    catalog = await make_catalog(session, "Каталог без остатка")
    category = await make_category(session, catalog.id, "Верхняя одежда")
    product = await make_product(session, catalog.id, category.id)
    product.run_out()
    await ProductRepository(session).save(product)

    page = await ShopQueries(session).list_products(category.id, 0, PAGE_SIZE)

    assert [(item.id, item.is_in_stock) for item in page.items] == [
        (product.id, False)
    ]


async def test_the_newest_product_comes_first(session: AsyncSession) -> None:
    catalog = await make_catalog(session, "Каталог с новинкой")
    category = await make_category(session, catalog.id, "Верхняя одежда")
    older = await make_product(session, catalog.id, category.id, "Пальто")
    await session.flush()
    newer = await make_product(session, catalog.id, category.id, "Куртка")
    await session.flush()

    page = await ShopQueries(session).list_products(category.id, 0, PAGE_SIZE)

    assert [item.id for item in page.items] == [newer.id, older.id]


async def test_a_hidden_product_cannot_be_opened(session: AsyncSession) -> None:
    catalog = await make_catalog(session, "Каталог со скрытой карточкой")
    category = await make_category(session, catalog.id, "Верхняя одежда")
    product = await make_product(session, catalog.id, category.id)
    product.hide()
    await ProductRepository(session).save(product)

    assert await ShopQueries(session).get_product(product.id) is None


async def test_a_card_carries_its_brand(session: AsyncSession) -> None:
    catalog = await make_catalog(session, "Каталог с брендом")
    category = await make_category(session, catalog.id, "Верхняя одежда")
    brand = await make_brand(session, "Acme")
    await session.flush()
    product = await make_product(session, catalog.id, category.id, brand_id=brand.id)
    await session.flush()

    view = await ShopQueries(session).get_product(product.id)

    assert view is not None
    assert view.brand_title == "Acme"


async def test_a_hidden_brand_is_not_named(session: AsyncSession) -> None:
    catalog = await make_catalog(session, "Каталог со скрытым брендом")
    category = await make_category(session, catalog.id, "Верхняя одежда")
    brand = await make_brand(session, "Скрытый бренд")
    await session.flush()
    product = await make_product(session, catalog.id, category.id, brand_id=brand.id)
    brand.archive()
    await BrandRepository(session).save(brand)

    view = await ShopQueries(session).get_product(product.id)

    assert view is not None
    assert view.brand_title is None


async def test_a_card_carries_its_media(session: AsyncSession) -> None:
    catalog = await make_catalog(session, "Каталог с медиа")
    category = await make_category(session, catalog.id, "Верхняя одежда")
    product = await make_product(session, catalog.id, category.id)
    await session.flush()
    media = ProductMediaRepository(session)
    await media.add(
        make_media(
            await media.next_id(), product_id=product.id, file_id="photo-front"
        )
    )
    await media.add(
        make_media(
            await media.next_id(),
            MediaKind.VIDEO,
            product_id=product.id,
            file_id="clip",
        )
    )
    await session.flush()

    view = await ShopQueries(session).get_product(product.id)

    assert view is not None
    assert view.photo_ids == ("photo-front",)
    assert view.video_id == "clip"


async def test_only_available_variants_reach_the_card(
    session: AsyncSession,
) -> None:
    catalog = await make_catalog(session, "Каталог с размерами")
    category = await make_category(session, catalog.id, "Верхняя одежда")
    product = await make_product(session, catalog.id, category.id)
    product.open_variants(Title("Размер"))
    await ProductRepository(session).save(product)
    variants = ProductVariantRepository(session)
    await variants.add(
        make_variant(await variants.next_id(), "M", product_id=product.id)
    )
    sold_out = make_variant(await variants.next_id(), "L", product_id=product.id)
    sold_out.run_out()
    await variants.add(sold_out)
    await session.flush()

    view = await ShopQueries(session).get_product(product.id)

    assert view is not None
    assert [variant.title for variant in view.variants] == ["M"]


async def test_a_variant_keeps_its_own_price(session: AsyncSession) -> None:
    catalog = await make_catalog(session, "Каталог с ценой размера")
    category = await make_category(session, catalog.id, "Верхняя одежда")
    product = await make_product(session, catalog.id, category.id)
    product.open_variants(Title("Размер"))
    await ProductRepository(session).save(product)
    variants = ProductVariantRepository(session)
    await variants.add(
        make_variant(
            await variants.next_id(),
            "L",
            product_id=product.id,
            price_override="13900",
        )
    )
    await session.flush()

    view = await ShopQueries(session).get_product(product.id)

    assert view is not None
    assert [variant.price for variant in view.variants] == [rub("13900")]


async def test_a_product_entry_carries_its_first_photo(
    session: AsyncSession,
) -> None:
    catalog = await make_catalog(session, "Каталог с миниатюрами")
    category = await make_category(session, catalog.id, "Верхняя одежда")
    product = await make_product(session, catalog.id, category.id)
    await session.flush()
    media = ProductMediaRepository(session)
    for position, file_id in enumerate(("photo-front", "photo-back")):
        await media.add(
            make_media(
                await media.next_id(),
                product_id=product.id,
                file_id=file_id,
                position=position,
            )
        )
    await session.flush()

    page = await ShopQueries(session).list_products(category.id, 0, PAGE_SIZE)

    assert [entry.thumbnail for entry in page.items] == ["photo-front"]


async def test_a_product_without_photos_has_no_thumbnail(
    session: AsyncSession,
) -> None:
    catalog = await make_catalog(session, "Каталог без фото")
    category = await make_category(session, catalog.id, "Верхняя одежда")
    await make_product(session, catalog.id, category.id)
    await session.flush()

    page = await ShopQueries(session).list_products(category.id, 0, PAGE_SIZE)

    assert page.items[0].thumbnail is None


async def test_a_category_knows_its_catalog_and_parent(
    session: AsyncSession,
) -> None:
    catalog = await make_catalog(session, "Одежда")
    parent = await make_category(session, catalog.id, "Верхняя одежда")
    child = await make_category(session, catalog.id, "Пальто", parent.id)
    await make_product(session, catalog.id, child.id)
    await session.flush()

    view = await ShopQueries(session).get_category(child.id)

    assert view is not None
    assert view.catalog_title == "Одежда"
    assert view.parent_title == "Верхняя одежда"


async def test_a_top_level_category_has_no_parent_title(
    session: AsyncSession,
) -> None:
    catalog = await make_catalog(session, "Каталог верхнего уровня")
    category = await make_category(session, catalog.id, "Верхняя одежда")
    await make_product(session, catalog.id, category.id)
    await session.flush()

    view = await ShopQueries(session).get_category(category.id)

    assert view is not None
    assert view.parent_title is None
