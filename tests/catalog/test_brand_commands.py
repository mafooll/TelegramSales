import pytest

from telegramsales.modules.catalog.application.commands.brands import (
    ChangeBrandVisibility,
    ChangeBrandVisibilityHandler,
    CreateBrand,
    CreateBrandHandler,
    DeleteBrand,
    DeleteBrandHandler,
    RenameBrand,
    RenameBrandHandler,
)
from telegramsales.modules.catalog.application.exceptions import (
    BrandNotFoundError,
    DuplicateTitleError,
)
from telegramsales.modules.catalog.contracts import BrandId
from telegramsales.modules.catalog.domain.permissions import CatalogPermission
from telegramsales.modules.catalog.domain.values import Title
from telegramsales.shared.application.access import PermissionDeniedError
from tests.catalog.factories import ACME, NOW, make_brand
from tests.catalog.fakes import (
    FakeBrandRepository,
    FakeCatalogUnitOfWork,
    FixedClock,
    actor_with,
)

MANAGER = actor_with(CatalogPermission.MANAGE)
OUTSIDER = actor_with()
MISSING = BrandId(404)


async def test_brand_is_created() -> None:
    uow = FakeCatalogUnitOfWork()

    brand_id = await CreateBrandHandler(uow, FixedClock(NOW)).handle(
        CreateBrand(title=Title("Acme")), MANAGER
    )

    assert uow.brands.items[brand_id].title == Title("Acme")


async def test_duplicate_brand_title_is_rejected() -> None:
    uow = FakeCatalogUnitOfWork(brands=FakeBrandRepository(make_brand()))

    with pytest.raises(DuplicateTitleError):
        await CreateBrandHandler(uow, FixedClock(NOW)).handle(
            CreateBrand(title=Title("Acme")), MANAGER
        )


async def test_outsider_cannot_create_a_brand() -> None:
    uow = FakeCatalogUnitOfWork()

    with pytest.raises(PermissionDeniedError):
        await CreateBrandHandler(uow, FixedClock(NOW)).handle(
            CreateBrand(title=Title("Acme")), OUTSIDER
        )


async def test_brand_is_renamed() -> None:
    uow = FakeCatalogUnitOfWork(brands=FakeBrandRepository(make_brand()))

    await RenameBrandHandler(uow).handle(
        RenameBrand(brand_id=ACME, title=Title("Acme Wear")), MANAGER
    )

    assert uow.brands.items[ACME].title == Title("Acme Wear")


async def test_renaming_a_missing_brand_is_rejected() -> None:
    uow = FakeCatalogUnitOfWork()

    with pytest.raises(BrandNotFoundError):
        await RenameBrandHandler(uow).handle(
            RenameBrand(brand_id=MISSING, title=Title("Acme")), MANAGER
        )


async def test_renaming_to_a_taken_title_is_rejected() -> None:
    uow = FakeCatalogUnitOfWork(
        brands=FakeBrandRepository(make_brand(), make_brand(BrandId(101), "Nike"))
    )

    with pytest.raises(DuplicateTitleError):
        await RenameBrandHandler(uow).handle(
            RenameBrand(brand_id=ACME, title=Title("Nike")), MANAGER
        )


async def test_brand_is_hidden_and_brought_back() -> None:
    uow = FakeCatalogUnitOfWork(brands=FakeBrandRepository(make_brand()))
    handler = ChangeBrandVisibilityHandler(uow)

    await handler.handle(
        ChangeBrandVisibility(brand_id=ACME, is_visible=False), MANAGER
    )
    hidden = uow.brands.items[ACME].is_active

    await handler.handle(
        ChangeBrandVisibility(brand_id=ACME, is_visible=True), MANAGER
    )

    assert not hidden
    assert uow.brands.items[ACME].is_active


async def test_brand_is_deleted() -> None:
    uow = FakeCatalogUnitOfWork(brands=FakeBrandRepository(make_brand()))

    await DeleteBrandHandler(uow).handle(DeleteBrand(brand_id=ACME), MANAGER)

    assert ACME not in uow.brands.items


async def test_deleting_a_missing_brand_is_rejected() -> None:
    uow = FakeCatalogUnitOfWork()

    with pytest.raises(BrandNotFoundError):
        await DeleteBrandHandler(uow).handle(DeleteBrand(brand_id=MISSING), MANAGER)


async def test_outsider_cannot_delete_a_brand() -> None:
    uow = FakeCatalogUnitOfWork(brands=FakeBrandRepository(make_brand()))

    with pytest.raises(PermissionDeniedError):
        await DeleteBrandHandler(uow).handle(DeleteBrand(brand_id=ACME), OUTSIDER)

    assert ACME in uow.brands.items
