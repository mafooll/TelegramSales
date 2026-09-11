import pytest

from telegramsales.modules.catalog.application.commands.variants import (
    AddVariant,
    AddVariantHandler,
    ChangeVariantAvailability,
    ChangeVariantAvailabilityHandler,
    ChangeVariantAxis,
    ChangeVariantAxisHandler,
    DeleteVariant,
    DeleteVariantHandler,
    RenameVariant,
    RenameVariantHandler,
    RepriceVariant,
    RepriceVariantHandler,
)
from telegramsales.modules.catalog.application.exceptions import (
    DuplicateTitleError,
    VariantNotFoundError,
)
from telegramsales.modules.catalog.contracts import VariantId
from telegramsales.modules.catalog.domain.entities import Product, ProductVariant
from telegramsales.modules.catalog.domain.exceptions import VariantsNotAllowedError
from telegramsales.modules.catalog.domain.permissions import CatalogPermission
from telegramsales.modules.catalog.domain.values import Title
from telegramsales.shared.application.access import PermissionDeniedError
from tests.catalog.factories import COAT, SIZE_M, make_product, make_variant, rub
from tests.catalog.fakes import (
    FakeCatalogUnitOfWork,
    FakeProductRepository,
    FakeProductVariantRepository,
    actor_with,
)

MANAGER = actor_with(CatalogPermission.MANAGE)
OUTSIDER = actor_with()
MISSING = VariantId(404)


def uow_with(
    product: Product,
    *variants: ProductVariant,
) -> FakeCatalogUnitOfWork:
    return FakeCatalogUnitOfWork(
        products=FakeProductRepository(product),
        variants=FakeProductVariantRepository(*variants),
    )


async def test_a_product_without_an_axis_takes_no_variants() -> None:
    uow = uow_with(make_product())

    with pytest.raises(VariantsNotAllowedError):
        await AddVariantHandler(uow).handle(
            AddVariant(product_id=COAT, title=Title("M")), MANAGER
        )


async def test_a_variant_is_added_once_the_axis_is_open() -> None:
    uow = uow_with(make_product(variant_label="Размер"))

    variant_id = await AddVariantHandler(uow).handle(
        AddVariant(product_id=COAT, title=Title("M")), MANAGER
    )

    assert uow.variants.items[variant_id].title == Title("M")


async def test_a_variant_may_carry_its_own_price() -> None:
    uow = uow_with(make_product(variant_label="Размер"))

    variant_id = await AddVariantHandler(uow).handle(
        AddVariant(product_id=COAT, title=Title("XL"), price_override=rub("14900")),
        MANAGER,
    )

    assert uow.variants.items[variant_id].price_override == rub("14900")


async def test_two_variants_may_not_share_a_title() -> None:
    uow = uow_with(make_product(variant_label="Размер"), make_variant())

    with pytest.raises(DuplicateTitleError):
        await AddVariantHandler(uow).handle(
            AddVariant(product_id=COAT, title=Title("M")), MANAGER
        )


async def test_outsider_cannot_add_a_variant() -> None:
    uow = uow_with(make_product(variant_label="Размер"))

    with pytest.raises(PermissionDeniedError):
        await AddVariantHandler(uow).handle(
            AddVariant(product_id=COAT, title=Title("M")), OUTSIDER
        )


async def test_the_axis_can_be_opened() -> None:
    uow = uow_with(make_product())

    await ChangeVariantAxisHandler(uow).handle(
        ChangeVariantAxis(product_id=COAT, label=Title("Размер")), MANAGER
    )

    assert uow.products.items[COAT].variant_label == Title("Размер")


async def test_the_axis_can_be_closed() -> None:
    uow = uow_with(make_product(variant_label="Размер"))

    await ChangeVariantAxisHandler(uow).handle(
        ChangeVariantAxis(product_id=COAT, label=None), MANAGER
    )

    assert not uow.products.items[COAT].has_variants


async def test_variant_is_renamed() -> None:
    uow = uow_with(make_product(variant_label="Размер"), make_variant())

    await RenameVariantHandler(uow).handle(
        RenameVariant(variant_id=SIZE_M, title=Title("L")), MANAGER
    )

    assert uow.variants.items[SIZE_M].title == Title("L")


async def test_renaming_to_a_sibling_title_is_rejected() -> None:
    uow = uow_with(
        make_product(variant_label="Размер"),
        make_variant(),
        make_variant(VariantId(501), "L"),
    )

    with pytest.raises(DuplicateTitleError):
        await RenameVariantHandler(uow).handle(
            RenameVariant(variant_id=SIZE_M, title=Title("L")), MANAGER
        )


async def test_renaming_a_missing_variant_is_rejected() -> None:
    uow = uow_with(make_product(variant_label="Размер"))

    with pytest.raises(VariantNotFoundError):
        await RenameVariantHandler(uow).handle(
            RenameVariant(variant_id=MISSING, title=Title("L")), MANAGER
        )


async def test_a_variant_price_can_be_dropped() -> None:
    uow = uow_with(
        make_product(variant_label="Размер"),
        make_variant(price_override="14900"),
    )

    await RepriceVariantHandler(uow).handle(
        RepriceVariant(variant_id=SIZE_M, price_override=None), MANAGER
    )

    assert uow.variants.items[SIZE_M].price_override is None


async def test_a_variant_runs_out_alone() -> None:
    uow = uow_with(make_product(variant_label="Размер"), make_variant())

    await ChangeVariantAvailabilityHandler(uow).handle(
        ChangeVariantAvailability(variant_id=SIZE_M, is_available=False), MANAGER
    )

    assert not uow.variants.items[SIZE_M].is_available
    assert uow.products.items[COAT].is_in_stock


async def test_variant_is_deleted() -> None:
    uow = uow_with(make_product(variant_label="Размер"), make_variant())

    await DeleteVariantHandler(uow).handle(DeleteVariant(variant_id=SIZE_M), MANAGER)

    assert SIZE_M not in uow.variants.items
