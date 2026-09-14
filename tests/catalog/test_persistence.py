import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from telegramsales.modules.catalog.contracts import CatalogId, CategoryId
from telegramsales.modules.catalog.domain.entities import (
    Brand,
    Catalog,
    Category,
    Product,
)
from telegramsales.modules.catalog.domain.values import Description, Title
from telegramsales.modules.catalog.infrastructure.queries import CatalogQueries
from telegramsales.modules.catalog.infrastructure.repositories import (
    BrandRepository,
    CatalogRepository,
    CategoryRepository,
    ProductRepository,
)
from tests.catalog.factories import NOW, usd

pytestmark = pytest.mark.db

PAGE_SIZE = 8


async def make_catalog(session: AsyncSession, title: str = "Одежда") -> Catalog:
    repository = CatalogRepository(session)
    catalog = Catalog.create(
        catalog_id=await repository.next_id(),
        title=Title(title),
        now=NOW,
    )
    await repository.add(catalog)
    return catalog


async def make_category(
    session: AsyncSession,
    catalog_id: CatalogId,
    title: str = "Верхняя одежда",
    parent_id: CategoryId | None = None,
) -> Category:
    repository = CategoryRepository(session)
    category = Category.create(
        category_id=await repository.next_id(),
        catalog_id=catalog_id,
        title=Title(title),
        now=NOW,
        parent_id=parent_id,
    )
    await repository.add(category)
    return category


async def test_identifiers_come_out_distinct(session: AsyncSession) -> None:
    repository = CatalogRepository(session)

    first, second = await repository.next_id(), await repository.next_id()

    assert first != second


async def test_catalog_survives_a_round_trip(session: AsyncSession) -> None:
    stored = await make_catalog(session)

    loaded = await CatalogRepository(session).get(stored.id)

    assert loaded is not None
    assert loaded.title == Title("Одежда")
    assert loaded.is_active
    assert loaded.created_at == NOW


async def test_missing_catalog_loads_as_none(session: AsyncSession) -> None:
    assert await CatalogRepository(session).get(CatalogId(404)) is None


async def test_archived_catalog_is_saved(session: AsyncSession) -> None:
    repository = CatalogRepository(session)
    catalog = await make_catalog(session)
    catalog.archive()
    await repository.save(catalog)

    loaded = await repository.get(catalog.id)

    assert loaded is not None
    assert not loaded.is_active


async def test_deleted_catalog_is_gone(session: AsyncSession) -> None:
    repository = CatalogRepository(session)
    catalog = await make_catalog(session)
    await repository.delete(catalog)

    assert await repository.get(catalog.id) is None


async def test_duplicate_catalog_title_is_seen(session: AsyncSession) -> None:
    await make_catalog(session)

    assert await CatalogRepository(session).exists_with_title(Title("Одежда"))


async def test_the_catalog_itself_can_keep_its_title(session: AsyncSession) -> None:
    catalog = await make_catalog(session)
    repository = CatalogRepository(session)

    assert not await repository.exists_with_title(
        Title("Одежда"), excluding=catalog.id
    )


async def test_duplicate_catalog_title_is_rejected_by_the_database(
    session: AsyncSession,
) -> None:
    await make_catalog(session)

    with pytest.raises(IntegrityError):
        async with session.begin_nested():
            await make_catalog(session)


async def test_category_survives_a_round_trip(session: AsyncSession) -> None:
    catalog = await make_catalog(session)
    stored = await make_category(session, catalog.id)

    loaded = await CategoryRepository(session).get(stored.id)

    assert loaded is not None
    assert loaded.catalog_id == catalog.id
    assert loaded.parent_id is None
    assert loaded.is_root


async def test_nested_category_keeps_its_parent(session: AsyncSession) -> None:
    catalog = await make_catalog(session)
    parent = await make_category(session, catalog.id)
    stored = await make_category(session, catalog.id, "Пальто", parent.id)

    loaded = await CategoryRepository(session).get(stored.id)

    assert loaded is not None
    assert loaded.parent_id == parent.id
    assert not loaded.is_root


async def test_two_root_categories_may_not_share_a_title(
    session: AsyncSession,
) -> None:
    catalog = await make_catalog(session)
    await make_category(session, catalog.id)

    with pytest.raises(IntegrityError):
        async with session.begin_nested():
            await make_category(session, catalog.id)


async def test_the_same_title_fits_under_different_parents(
    session: AsyncSession,
) -> None:
    catalog = await make_catalog(session)
    first = await make_category(session, catalog.id, "Женское")
    second = await make_category(session, catalog.id, "Мужское")

    await make_category(session, catalog.id, "Пальто", first.id)
    await make_category(session, catalog.id, "Пальто", second.id)

    assert await CategoryRepository(session).count_in_catalog(catalog.id) == 4


async def test_children_are_counted(session: AsyncSession) -> None:
    catalog = await make_catalog(session)
    parent = await make_category(session, catalog.id)
    await make_category(session, catalog.id, "Пальто", parent.id)
    await make_category(session, catalog.id, "Куртки", parent.id)

    assert await CategoryRepository(session).count_children(parent.id) == 2


async def test_a_root_category_without_children_counts_zero(
    session: AsyncSession,
) -> None:
    catalog = await make_catalog(session)
    category = await make_category(session, catalog.id)

    assert await CategoryRepository(session).count_children(category.id) == 0


async def test_brand_survives_a_round_trip(session: AsyncSession) -> None:
    repository = BrandRepository(session)
    brand = Brand.create(
        brand_id=await repository.next_id(),
        title=Title("Acme"),
        now=NOW,
    )
    await repository.add(brand)

    loaded = await repository.get(brand.id)

    assert loaded is not None
    assert loaded.title == Title("Acme")


async def test_catalog_view_counts_its_categories(session: AsyncSession) -> None:
    catalog = await make_catalog(session)
    await make_category(session, catalog.id, "Верхняя одежда")
    await make_category(session, catalog.id, "Платья")

    view = await CatalogQueries(session).get_catalog(catalog.id)

    assert view is not None
    assert view.title == "Одежда"
    assert view.category_count == 2


async def test_catalog_view_counts_its_uncategorized_products(
    session: AsyncSession,
) -> None:
    catalog = await make_catalog(session)
    category = await make_category(session, catalog.id)
    repository = ProductRepository(session)
    await repository.add(
        Product.create(
            product_id=await repository.next_id(),
            catalog_id=catalog.id,
            category_id=None,
            title=Title("Без категории"),
            description=Description("Тёплое пальто из шерсти."),
            article=await repository.next_article(),
            price=usd("12900"),
            now=NOW,
        )
    )
    await repository.add(
        Product.create(
            product_id=await repository.next_id(),
            catalog_id=catalog.id,
            category_id=category.id,
            title=Title("С категорией"),
            description=Description("Тёплое пальто из шерсти."),
            article=await repository.next_article(),
            price=usd("12900"),
            now=NOW,
        )
    )

    view = await CatalogQueries(session).get_catalog(catalog.id)

    assert view is not None
    assert view.uncategorized_product_count == 1


async def test_catalog_view_of_a_missing_catalog_is_none(
    session: AsyncSession,
) -> None:
    assert await CatalogQueries(session).get_catalog(CatalogId(404)) is None


async def test_catalogs_are_listed_alphabetically(session: AsyncSession) -> None:
    await make_catalog(session, "Одежда")
    await make_catalog(session, "Бьюти")

    page = await CatalogQueries(session).list_catalogs(0, PAGE_SIZE)

    assert [item.title for item in page.items] == ["Бьюти", "Одежда"]
    assert page.total == 2


async def test_category_view_counts_its_children(session: AsyncSession) -> None:
    catalog = await make_catalog(session)
    parent = await make_category(session, catalog.id)
    await make_category(session, catalog.id, "Пальто", parent.id)

    view = await CatalogQueries(session).get_category(parent.id)

    assert view is not None
    assert view.child_count == 1
    assert view.parent_id is None


async def test_root_categories_are_listed_without_their_children(
    session: AsyncSession,
) -> None:
    catalog = await make_catalog(session)
    parent = await make_category(session, catalog.id)
    await make_category(session, catalog.id, "Пальто", parent.id)

    page = await CatalogQueries(session).list_categories(
        catalog.id, None, 0, PAGE_SIZE
    )

    assert [item.title for item in page.items] == ["Верхняя одежда"]


async def test_children_are_listed_under_their_parent(
    session: AsyncSession,
) -> None:
    catalog = await make_catalog(session)
    parent = await make_category(session, catalog.id)
    await make_category(session, catalog.id, "Пальто", parent.id)
    await make_category(session, catalog.id, "Куртки", parent.id)

    page = await CatalogQueries(session).list_categories(
        catalog.id, parent.id, 0, PAGE_SIZE
    )

    assert [item.title for item in page.items] == ["Куртки", "Пальто"]


async def test_categories_of_another_catalog_do_not_leak(
    session: AsyncSession,
) -> None:
    clothes = await make_catalog(session, "Одежда")
    beauty = await make_catalog(session, "Бьюти")
    await make_category(session, clothes.id, "Платья")

    page = await CatalogQueries(session).list_categories(
        beauty.id, None, 0, PAGE_SIZE
    )

    assert page.total == 0


async def test_listing_paginates(session: AsyncSession) -> None:
    for number in range(3):
        await make_catalog(session, f"Каталог {number}")

    page = await CatalogQueries(session).list_catalogs(1, 2)

    assert page.total == 3
    assert len(page.items) == 1
