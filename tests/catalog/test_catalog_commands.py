import pytest

from telegramsales.modules.catalog.application.commands.catalogs import (
    ChangeCatalogVisibility,
    ChangeCatalogVisibilityHandler,
    CreateCatalog,
    CreateCatalogHandler,
    DeleteCatalog,
    DeleteCatalogHandler,
    RenameCatalog,
    RenameCatalogHandler,
)
from telegramsales.modules.catalog.application.exceptions import (
    CatalogNotFoundError,
    DuplicateTitleError,
)
from telegramsales.modules.catalog.contracts import CatalogId
from telegramsales.modules.catalog.domain.exceptions import (
    CatalogHoldsProductsError,
    CatalogNotEmptyError,
)
from telegramsales.modules.catalog.domain.permissions import CatalogPermission
from telegramsales.modules.catalog.domain.values import Title
from telegramsales.shared.application.access import PermissionDeniedError
from tests.catalog.factories import (
    CLOTHES,
    NOW,
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
MISSING = CatalogId(404)


def create_handler(uow: FakeCatalogUnitOfWork) -> CreateCatalogHandler:
    return CreateCatalogHandler(uow, FixedClock(NOW))


async def test_created_catalog_is_stored() -> None:
    uow = FakeCatalogUnitOfWork()

    catalog_id = await create_handler(uow).handle(
        CreateCatalog(title=Title("Одежда")), MANAGER
    )

    assert uow.catalogs.items[catalog_id].title == Title("Одежда")


async def test_created_catalog_takes_the_current_moment() -> None:
    uow = FakeCatalogUnitOfWork()

    catalog_id = await create_handler(uow).handle(
        CreateCatalog(title=Title("Одежда")), MANAGER
    )

    assert uow.catalogs.items[catalog_id].created_at == NOW


async def test_created_catalog_is_visible() -> None:
    uow = FakeCatalogUnitOfWork()

    catalog_id = await create_handler(uow).handle(
        CreateCatalog(title=Title("Одежда")), MANAGER
    )

    assert uow.catalogs.items[catalog_id].is_active


async def test_creation_commits() -> None:
    uow = FakeCatalogUnitOfWork()

    await create_handler(uow).handle(CreateCatalog(title=Title("Одежда")), MANAGER)

    assert uow.committed


async def test_outsider_cannot_create_a_catalog() -> None:
    uow = FakeCatalogUnitOfWork()

    with pytest.raises(PermissionDeniedError):
        await create_handler(uow).handle(
            CreateCatalog(title=Title("Одежда")), OUTSIDER
        )

    assert not uow.catalogs.items


async def test_duplicate_title_is_rejected() -> None:
    uow = FakeCatalogUnitOfWork(catalogs=FakeCatalogRepository(make_catalog()))

    with pytest.raises(DuplicateTitleError):
        await create_handler(uow).handle(
            CreateCatalog(title=Title("Одежда")), MANAGER
        )


async def test_rejected_creation_rolls_back() -> None:
    uow = FakeCatalogUnitOfWork(catalogs=FakeCatalogRepository(make_catalog()))

    with pytest.raises(DuplicateTitleError):
        await create_handler(uow).handle(
            CreateCatalog(title=Title("Одежда")), MANAGER
        )

    assert uow.rolled_back
    assert not uow.committed


async def test_catalog_is_renamed() -> None:
    uow = FakeCatalogUnitOfWork(catalogs=FakeCatalogRepository(make_catalog()))

    await RenameCatalogHandler(uow).handle(
        RenameCatalog(catalog_id=CLOTHES, title=Title("Женская одежда")), MANAGER
    )

    assert uow.catalogs.items[CLOTHES].title == Title("Женская одежда")


async def test_renaming_to_its_own_title_is_allowed() -> None:
    uow = FakeCatalogUnitOfWork(catalogs=FakeCatalogRepository(make_catalog()))

    await RenameCatalogHandler(uow).handle(
        RenameCatalog(catalog_id=CLOTHES, title=Title("  Одежда  ")), MANAGER
    )

    assert uow.catalogs.items[CLOTHES].title == Title("Одежда")


async def test_renaming_to_a_taken_title_is_rejected() -> None:
    uow = FakeCatalogUnitOfWork(
        catalogs=FakeCatalogRepository(
            make_catalog(),
            make_catalog(CatalogId(2), "Бьюти"),
        )
    )

    with pytest.raises(DuplicateTitleError):
        await RenameCatalogHandler(uow).handle(
            RenameCatalog(catalog_id=CLOTHES, title=Title("Бьюти")), MANAGER
        )


async def test_renaming_a_missing_catalog_is_rejected() -> None:
    uow = FakeCatalogUnitOfWork()

    with pytest.raises(CatalogNotFoundError):
        await RenameCatalogHandler(uow).handle(
            RenameCatalog(catalog_id=MISSING, title=Title("Одежда")), MANAGER
        )


async def test_outsider_cannot_rename() -> None:
    uow = FakeCatalogUnitOfWork(catalogs=FakeCatalogRepository(make_catalog()))

    with pytest.raises(PermissionDeniedError):
        await RenameCatalogHandler(uow).handle(
            RenameCatalog(catalog_id=CLOTHES, title=Title("Другое")), OUTSIDER
        )


async def test_catalog_is_hidden() -> None:
    uow = FakeCatalogUnitOfWork(catalogs=FakeCatalogRepository(make_catalog()))

    await ChangeCatalogVisibilityHandler(uow).handle(
        ChangeCatalogVisibility(catalog_id=CLOTHES, is_visible=False), MANAGER
    )

    assert not uow.catalogs.items[CLOTHES].is_active


async def test_hidden_catalog_is_brought_back() -> None:
    catalog = make_catalog()
    catalog.archive()
    uow = FakeCatalogUnitOfWork(catalogs=FakeCatalogRepository(catalog))

    await ChangeCatalogVisibilityHandler(uow).handle(
        ChangeCatalogVisibility(catalog_id=CLOTHES, is_visible=True), MANAGER
    )

    assert uow.catalogs.items[CLOTHES].is_active


async def test_empty_catalog_is_deleted() -> None:
    uow = FakeCatalogUnitOfWork(catalogs=FakeCatalogRepository(make_catalog()))

    await DeleteCatalogHandler(uow).handle(
        DeleteCatalog(catalog_id=CLOTHES), MANAGER
    )

    assert CLOTHES not in uow.catalogs.items


async def test_catalog_with_its_own_products_survives_deletion() -> None:
    product = make_product()
    product.move_to(CLOTHES, None)
    uow = FakeCatalogUnitOfWork(
        catalogs=FakeCatalogRepository(make_catalog()),
        products=FakeProductRepository(product),
    )

    with pytest.raises(CatalogHoldsProductsError):
        await DeleteCatalogHandler(uow).handle(
            DeleteCatalog(catalog_id=CLOTHES), MANAGER
        )

    assert CLOTHES in uow.catalogs.items


async def test_catalog_with_categories_survives_deletion() -> None:
    uow = FakeCatalogUnitOfWork(
        catalogs=FakeCatalogRepository(make_catalog()),
        categories=FakeCategoryRepository(make_category()),
    )

    with pytest.raises(CatalogNotEmptyError):
        await DeleteCatalogHandler(uow).handle(
            DeleteCatalog(catalog_id=CLOTHES), MANAGER
        )

    assert CLOTHES in uow.catalogs.items


async def test_deleting_a_missing_catalog_is_rejected() -> None:
    uow = FakeCatalogUnitOfWork()

    with pytest.raises(CatalogNotFoundError):
        await DeleteCatalogHandler(uow).handle(
            DeleteCatalog(catalog_id=MISSING), MANAGER
        )


async def test_outsider_cannot_delete() -> None:
    uow = FakeCatalogUnitOfWork(catalogs=FakeCatalogRepository(make_catalog()))

    with pytest.raises(PermissionDeniedError):
        await DeleteCatalogHandler(uow).handle(
            DeleteCatalog(catalog_id=CLOTHES), OUTSIDER
        )

    assert CLOTHES in uow.catalogs.items
