import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from telegramsales.modules.catalog.domain.entities import Product
from telegramsales.modules.catalog.domain.enums import MediaKind
from telegramsales.modules.catalog.domain.values import Article, Description, Title
from telegramsales.modules.catalog.infrastructure.queries import ProductQueries
from telegramsales.modules.catalog.infrastructure.repositories import (
    ProductMediaRepository,
    ProductRepository,
    ProductVariantRepository,
)
from tests.catalog.factories import NOW, make_media, make_variant, usd
from tests.catalog.test_persistence import make_catalog, make_category

pytestmark = pytest.mark.db

PAGE_SIZE = 8


async def store_product(
    session: AsyncSession,
    title: str = "Пальто оверсайз",
    *,
    price: str = "12900",
) -> Product:
    catalog = await make_catalog(session, f"Каталог {title}")
    category = await make_category(session, catalog.id, f"Категория {title}")
    repository = ProductRepository(session)
    product = Product.create(
        product_id=await repository.next_id(),
        catalog_id=catalog.id,
        category_id=category.id,
        title=Title(title),
        description=Description("Тёплое пальто из шерсти."),
        article=await repository.next_article(),
        price=usd(price),
        now=NOW,
    )
    await repository.add(product)
    return product


async def test_articles_come_out_distinct(session: AsyncSession) -> None:
    repository = ProductRepository(session)

    first, second = await repository.next_article(), await repository.next_article()

    assert first != second


async def test_article_is_padded(session: AsyncSession) -> None:
    article = await ProductRepository(session).next_article()

    assert article.value.isdigit()


async def test_product_survives_a_round_trip(session: AsyncSession) -> None:
    stored = await store_product(session)

    loaded = await ProductRepository(session).get(stored.id)

    assert loaded is not None
    assert loaded.title == Title("Пальто оверсайз")
    assert loaded.price == usd("12900")
    assert loaded.old_price is None
    assert not loaded.is_published


async def test_a_sale_price_survives_a_round_trip(session: AsyncSession) -> None:
    repository = ProductRepository(session)
    product = await store_product(session)
    product.reprice(usd("9900"), usd("12900"))
    await repository.save(product)

    loaded = await repository.get(product.id)

    assert loaded is not None
    assert loaded.is_on_sale
    assert loaded.old_price == usd("12900")


async def test_publication_survives_a_round_trip(session: AsyncSession) -> None:
    repository = ProductRepository(session)
    product = await store_product(session)
    product.publish(NOW)
    await repository.save(product)

    loaded = await repository.get(product.id)

    assert loaded is not None
    assert loaded.published_at == NOW


async def test_duplicate_article_is_rejected(session: AsyncSession) -> None:
    repository = ProductRepository(session)
    first = await store_product(session, "Первое")
    second = await store_product(session, "Второе")
    second.article = Article(first.article.value)

    with pytest.raises(IntegrityError):
        async with session.begin_nested():
            await repository.save(second)


async def test_products_are_counted_in_their_category(
    session: AsyncSession,
) -> None:
    product = await store_product(session)
    assert product.category_id is not None

    counted = await ProductRepository(session).count_in_category(product.category_id)

    assert counted == 1


async def test_variant_survives_a_round_trip(session: AsyncSession) -> None:
    product = await store_product(session)
    repository = ProductVariantRepository(session)
    variant = make_variant(await repository.next_id(), "M", product_id=product.id)
    await repository.add(variant)

    loaded = await repository.get(variant.id)

    assert loaded is not None
    assert loaded.title == Title("M")
    assert loaded.is_available


async def test_two_variants_may_not_share_a_title(session: AsyncSession) -> None:
    product = await store_product(session)
    repository = ProductVariantRepository(session)
    await repository.add(
        make_variant(await repository.next_id(), "M", product_id=product.id)
    )

    with pytest.raises(IntegrityError):
        async with session.begin_nested():
            await repository.add(
                make_variant(await repository.next_id(), "M", product_id=product.id)
            )


async def test_variants_are_counted(session: AsyncSession) -> None:
    product = await store_product(session)
    repository = ProductVariantRepository(session)
    for title in ("S", "M", "L"):
        await repository.add(
            make_variant(await repository.next_id(), title, product_id=product.id)
        )

    assert await repository.count_for(product.id) == 3


async def test_media_is_counted_by_kind(session: AsyncSession) -> None:
    product = await store_product(session)
    repository = ProductMediaRepository(session)
    for index in range(2):
        await repository.add(
            make_media(
                await repository.next_id(),
                product_id=product.id,
                file_id=f"photo-{index}",
            )
        )
    await repository.add(
        make_media(
            await repository.next_id(),
            MediaKind.VIDEO,
            product_id=product.id,
            file_id="clip",
        )
    )

    assert await repository.count_of_kind(product.id, MediaKind.PHOTO) == 2
    assert await repository.count_of_kind(product.id, MediaKind.VIDEO) == 1


async def test_product_view_counts_media_and_variants(
    session: AsyncSession,
) -> None:
    product = await store_product(session)
    media = ProductMediaRepository(session)
    await media.add(
        make_media(await media.next_id(), product_id=product.id, file_id="photo")
    )
    variants = ProductVariantRepository(session)
    await variants.add(
        make_variant(await variants.next_id(), "M", product_id=product.id)
    )

    view = await ProductQueries(session).get_product(product.id)

    assert view is not None
    assert view.photo_count == 1
    assert view.video_count == 0
    assert view.variant_count == 1
    assert view.brand_title is None


async def test_missing_product_view_is_none(session: AsyncSession) -> None:
    product = await store_product(session)
    await ProductRepository(session).delete(product)

    assert await ProductQueries(session).get_product(product.id) is None


async def test_variant_view_falls_back_to_the_product_price(
    session: AsyncSession,
) -> None:
    product = await store_product(session, price="12900")
    repository = ProductVariantRepository(session)
    await repository.add(
        make_variant(await repository.next_id(), "M", product_id=product.id)
    )

    views = await ProductQueries(session).list_variants(product.id)

    assert [view.price for view in views] == [usd("12900")]


async def test_variant_view_uses_its_own_price(session: AsyncSession) -> None:
    product = await store_product(session, price="12900")
    repository = ProductVariantRepository(session)
    await repository.add(
        make_variant(
            await repository.next_id(),
            "L",
            product_id=product.id,
            price_override="14900",
        )
    )

    views = await ProductQueries(session).list_variants(product.id)

    assert [view.price for view in views] == [usd("14900")]


async def test_products_are_listed_within_their_category(
    session: AsyncSession,
) -> None:
    product = await store_product(session)

    page = await ProductQueries(session).list_products(
        product.catalog_id, product.category_id, 0, PAGE_SIZE
    )

    assert [item.title for item in page.items] == ["Пальто оверсайз"]
    assert page.total == 1


async def test_a_product_can_be_stored_without_a_category(
    session: AsyncSession,
) -> None:
    catalog = await make_catalog(session, "Каталог без категорий")
    repository = ProductRepository(session)
    product = Product.create(
        product_id=await repository.next_id(),
        catalog_id=catalog.id,
        category_id=None,
        title=Title("Пальто без категории"),
        description=Description("Тёплое пальто из шерсти."),
        article=await repository.next_article(),
        price=usd("12900"),
        now=NOW,
    )
    await repository.add(product)

    loaded = await repository.get(product.id)

    assert loaded is not None
    assert loaded.category_id is None


async def test_uncategorized_products_are_listed_under_their_catalog(
    session: AsyncSession,
) -> None:
    catalog = await make_catalog(session, "Каталог с товаром без категории")
    category = await make_category(session, catalog.id, "Категория")
    repository = ProductRepository(session)
    categorized = Product.create(
        product_id=await repository.next_id(),
        catalog_id=catalog.id,
        category_id=category.id,
        title=Title("С категорией"),
        description=Description("Тёплое пальто из шерсти."),
        article=await repository.next_article(),
        price=usd("12900"),
        now=NOW,
    )
    uncategorized = Product.create(
        product_id=await repository.next_id(),
        catalog_id=catalog.id,
        category_id=None,
        title=Title("Без категории"),
        description=Description("Тёплое пальто из шерсти."),
        article=await repository.next_article(),
        price=usd("12900"),
        now=NOW,
    )
    await repository.add(categorized)
    await repository.add(uncategorized)

    page = await ProductQueries(session).list_products(
        catalog.id, None, 0, PAGE_SIZE
    )

    assert [item.id for item in page.items] == [uncategorized.id]


async def test_deleting_a_product_takes_its_media_along(
    session: AsyncSession,
) -> None:
    product = await store_product(session)
    media = ProductMediaRepository(session)
    await media.add(
        make_media(await media.next_id(), product_id=product.id, file_id="photo")
    )

    await ProductRepository(session).delete(product)

    assert await ProductQueries(session).list_media(product.id) == []
