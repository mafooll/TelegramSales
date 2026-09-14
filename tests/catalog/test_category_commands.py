import pytest

from telegramsales.modules.catalog.application.commands.categories import (
    ChangeCategoryVisibility,
    ChangeCategoryVisibilityHandler,
    CreateCategory,
    CreateCategoryHandler,
    DeleteCategory,
    DeleteCategoryHandler,
    RenameCategory,
    RenameCategoryHandler,
)
from telegramsales.modules.catalog.application.exceptions import (
    CatalogNotFoundError,
    CategoryNotFoundError,
    DuplicateTitleError,
)
from telegramsales.modules.catalog.contracts import CatalogId, CategoryId
from telegramsales.modules.catalog.domain.entities import Category
from telegramsales.modules.catalog.domain.exceptions import (
    CatalogHoldsProductsError,
    CategoryNotEmptyError,
    ForeignCatalogError,
    NestingTooDeepError,
)
from telegramsales.modules.catalog.domain.permissions import CatalogPermission
from telegramsales.modules.catalog.domain.values import Title
from telegramsales.shared.application.access import PermissionDeniedError
from tests.catalog.factories import (
    BEAUTY,
    CLOTHES,
    COATS,
    NOW,
    OUTERWEAR,
    make_catalog,
    make_category,
    make_product,
)
from tests.catalog.fakes import (
    FakeCatalogRepository,
    FakeCatalogUnitOfWork,
    FakeCategoryRepository,
    FakeProductRepository,
    FixedClock,
    actor_with,
)

MANAGER = actor_with(CatalogPermission.MANAGE)
OUTSIDER = actor_with()
MISSING = CategoryId(404)


def uow_with(*categories: Category) -> FakeCatalogUnitOfWork:
    return FakeCatalogUnitOfWork(
        catalogs=FakeCatalogRepository(
            make_catalog(CLOTHES, "Одежда"),
            make_catalog(BEAUTY, "Бьюти"),
        ),
        categories=FakeCategoryRepository(*categories),
    )


def create_handler(uow: FakeCatalogUnitOfWork) -> CreateCategoryHandler:
    return CreateCategoryHandler(uow, FixedClock(NOW))


def uow_holding_a_bare_product() -> FakeCatalogUnitOfWork:
    product = make_product()
    product.move_to(CLOTHES, None)
    return FakeCatalogUnitOfWork(
        catalogs=FakeCatalogRepository(make_catalog(CLOTHES, "Одежда")),
        categories=FakeCategoryRepository(),
        products=FakeProductRepository(product),
    )


async def test_a_catalog_with_bare_products_takes_no_categories() -> None:
    uow = uow_holding_a_bare_product()
    command = CreateCategory(catalog_id=CLOTHES, title=Title("Верхняя одежда"))

    with pytest.raises(CatalogHoldsProductsError):
        await create_handler(uow).handle(command, MANAGER)


async def test_root_category_is_created() -> None:
    uow = uow_with()

    category_id = await create_handler(uow).handle(
        CreateCategory(catalog_id=CLOTHES, title=Title("Платья")), MANAGER
    )

    created = uow.categories.items[category_id]
    assert created.is_root
    assert created.catalog_id == CLOTHES


async def test_nested_category_is_created_under_a_root() -> None:
    uow = uow_with(make_category())

    category_id = await create_handler(uow).handle(
        CreateCategory(
            catalog_id=CLOTHES, title=Title("Пальто"), parent_id=OUTERWEAR
        ),
        MANAGER,
    )

    assert uow.categories.items[category_id].parent_id == OUTERWEAR


async def test_third_level_is_rejected() -> None:
    nested = make_category(COATS, "Пальто", parent_id=OUTERWEAR)
    uow = uow_with(make_category(), nested)

    with pytest.raises(NestingTooDeepError):
        await create_handler(uow).handle(
            CreateCategory(
                catalog_id=CLOTHES, title=Title("Драповые"), parent_id=COATS
            ),
            MANAGER,
        )


async def test_parent_from_another_catalog_is_rejected() -> None:
    uow = uow_with(make_category())

    with pytest.raises(ForeignCatalogError):
        await create_handler(uow).handle(
            CreateCategory(
                catalog_id=BEAUTY, title=Title("Пальто"), parent_id=OUTERWEAR
            ),
            MANAGER,
        )


async def test_missing_parent_is_rejected() -> None:
    uow = uow_with()

    with pytest.raises(CategoryNotFoundError):
        await create_handler(uow).handle(
            CreateCategory(
                catalog_id=CLOTHES, title=Title("Пальто"), parent_id=MISSING
            ),
            MANAGER,
        )


async def test_missing_catalog_is_rejected() -> None:
    uow = uow_with()

    with pytest.raises(CatalogNotFoundError):
        await create_handler(uow).handle(
            CreateCategory(catalog_id=CatalogId(404), title=Title("Платья")),
            MANAGER,
        )


async def test_duplicate_title_under_the_same_parent_is_rejected() -> None:
    uow = uow_with(make_category())

    with pytest.raises(DuplicateTitleError):
        await create_handler(uow).handle(
            CreateCategory(catalog_id=CLOTHES, title=Title("Верхняя одежда")),
            MANAGER,
        )


async def test_the_same_title_fits_under_a_different_parent() -> None:
    uow = uow_with(make_category())

    category_id = await create_handler(uow).handle(
        CreateCategory(
            catalog_id=CLOTHES, title=Title("Верхняя одежда"), parent_id=OUTERWEAR
        ),
        MANAGER,
    )

    assert category_id in uow.categories.items


async def test_the_same_title_fits_in_another_catalog() -> None:
    uow = uow_with(make_category())

    category_id = await create_handler(uow).handle(
        CreateCategory(catalog_id=BEAUTY, title=Title("Верхняя одежда")), MANAGER
    )

    assert uow.categories.items[category_id].catalog_id == BEAUTY


async def test_outsider_cannot_create_a_category() -> None:
    uow = uow_with()

    with pytest.raises(PermissionDeniedError):
        await create_handler(uow).handle(
            CreateCategory(catalog_id=CLOTHES, title=Title("Платья")), OUTSIDER
        )


async def test_category_is_renamed() -> None:
    uow = uow_with(make_category())

    await RenameCategoryHandler(uow).handle(
        RenameCategory(category_id=OUTERWEAR, title=Title("Верхнее")), MANAGER
    )

    assert uow.categories.items[OUTERWEAR].title == Title("Верхнее")


async def test_renaming_collides_only_within_the_same_parent() -> None:
    nested = make_category(COATS, "Пальто", parent_id=OUTERWEAR)
    uow = uow_with(make_category(), nested)

    await RenameCategoryHandler(uow).handle(
        RenameCategory(category_id=COATS, title=Title("Верхняя одежда")), MANAGER
    )

    assert uow.categories.items[COATS].title == Title("Верхняя одежда")


async def test_renaming_to_a_sibling_title_is_rejected() -> None:
    sibling = make_category(CategoryId(12), "Платья")
    uow = uow_with(make_category(), sibling)

    with pytest.raises(DuplicateTitleError):
        await RenameCategoryHandler(uow).handle(
            RenameCategory(category_id=OUTERWEAR, title=Title("Платья")), MANAGER
        )


async def test_category_is_hidden_and_brought_back() -> None:
    uow = uow_with(make_category())
    handler = ChangeCategoryVisibilityHandler(uow)

    await handler.handle(
        ChangeCategoryVisibility(category_id=OUTERWEAR, is_visible=False), MANAGER
    )
    hidden = uow.categories.items[OUTERWEAR].is_active

    await handler.handle(
        ChangeCategoryVisibility(category_id=OUTERWEAR, is_visible=True), MANAGER
    )

    assert not hidden
    assert uow.categories.items[OUTERWEAR].is_active


async def test_leaf_category_is_deleted() -> None:
    uow = uow_with(make_category())

    await DeleteCategoryHandler(uow).handle(
        DeleteCategory(category_id=OUTERWEAR), MANAGER
    )

    assert OUTERWEAR not in uow.categories.items


async def test_category_with_children_survives_deletion() -> None:
    nested = make_category(COATS, "Пальто", parent_id=OUTERWEAR)
    uow = uow_with(make_category(), nested)

    with pytest.raises(CategoryNotEmptyError):
        await DeleteCategoryHandler(uow).handle(
            DeleteCategory(category_id=OUTERWEAR), MANAGER
        )

    assert OUTERWEAR in uow.categories.items


async def test_deleting_a_missing_category_is_rejected() -> None:
    uow = uow_with()

    with pytest.raises(CategoryNotFoundError):
        await DeleteCategoryHandler(uow).handle(
            DeleteCategory(category_id=MISSING), MANAGER
        )
