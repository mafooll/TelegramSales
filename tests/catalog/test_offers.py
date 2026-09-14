from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from telegramsales.modules.catalog.contracts import MediaLayout, ProductId, VariantId
from telegramsales.modules.catalog.domain.entities import Product, ProductVariant
from telegramsales.modules.catalog.domain.values import Title
from telegramsales.modules.catalog.infrastructure.offers import CatalogOffers
from telegramsales.modules.catalog.infrastructure.repositories import (
    ProductMediaRepository,
    ProductRepository,
    ProductVariantRepository,
)
from tests.catalog.factories import make_media, usd
from tests.catalog.test_product_persistence import store_product

pytestmark = pytest.mark.db


async def publish(session: AsyncSession, product: Product) -> Product:
    await ProductRepository(session).save(product)
    return product


async def add_variant(
    session: AsyncSession,
    product: Product,
    title: str = "M",
    *,
    price_override: str | None = None,
    available: bool = True,
) -> VariantId:
    repository = ProductVariantRepository(session)
    variant = ProductVariant.create(
        variant_id=await repository.next_id(),
        product_id=product.id,
        title=Title(title),
        price_override=None if price_override is None else usd(price_override),
    )
    if not available:
        variant.run_out()
    await repository.add(variant)
    return variant.id


async def offered(session: AsyncSession, title: str) -> Product:
    product = await store_product(session, title)
    product.publish(product.created_at)
    return await publish(session, product)


async def test_a_published_product_is_on_offer(session: AsyncSession) -> None:
    product = await offered(session, "Пальто предложенное")

    offer = await CatalogOffers(session).offer(product.id, None)

    assert offer is not None
    assert offer.is_available
    assert offer.price == usd("12900")
    assert offer.title == "Пальто предложенное"


async def test_an_offer_carries_its_photos(session: AsyncSession) -> None:
    product = await offered(session, "Пальто с фото")
    media = ProductMediaRepository(session)
    await media.add(
        make_media(await media.next_id(), product_id=product.id, file_id="front")
    )
    await media.add(
        make_media(await media.next_id(), product_id=product.id, file_id="back")
    )

    offer = await CatalogOffers(session).offer(product.id, None)

    assert offer is not None
    assert offer.photo_ids == ("front", "back")
    assert offer.media_layout == MediaLayout.COLLAGE


async def test_a_draft_product_is_not_on_offer(session: AsyncSession) -> None:
    product = await store_product(session, "Пальто черновик")

    offer = await CatalogOffers(session).offer(product.id, None)

    assert offer is not None
    assert not offer.is_available


async def test_a_hidden_product_is_not_on_offer(session: AsyncSession) -> None:
    product = await offered(session, "Пальто скрытое")
    product.hide()
    await publish(session, product)

    offer = await CatalogOffers(session).offer(product.id, None)

    assert offer is not None
    assert not offer.is_available


async def test_a_sold_out_product_is_not_on_offer(session: AsyncSession) -> None:
    product = await offered(session, "Пальто без остатка")
    product.run_out()
    await publish(session, product)

    offer = await CatalogOffers(session).offer(product.id, None)

    assert offer is not None
    assert not offer.is_available


async def test_an_unknown_product_has_no_offer(session: AsyncSession) -> None:
    offer = await CatalogOffers(session).offer(ProductId(uuid4()), None)

    assert offer is None


async def test_a_variant_carries_its_own_title(session: AsyncSession) -> None:
    product = await offered(session, "Пальто с размером")
    variant_id = await add_variant(session, product)

    offer = await CatalogOffers(session).offer(product.id, variant_id)

    assert offer is not None
    assert offer.variant_title == "M"
    assert offer.is_available


async def test_a_variant_price_wins(session: AsyncSession) -> None:
    product = await offered(session, "Пальто с ценой размера")
    variant_id = await add_variant(session, product, price_override="13900")

    offer = await CatalogOffers(session).offer(product.id, variant_id)

    assert offer is not None
    assert offer.price == usd("13900")


async def test_a_sold_out_variant_is_not_on_offer(session: AsyncSession) -> None:
    product = await offered(session, "Пальто без размера")
    variant_id = await add_variant(session, product, available=False)

    offer = await CatalogOffers(session).offer(product.id, variant_id)

    assert offer is not None
    assert not offer.is_available


async def test_an_unknown_variant_has_no_offer(session: AsyncSession) -> None:
    product = await offered(session, "Пальто чужой размер")

    offer = await CatalogOffers(session).offer(product.id, VariantId(999999))

    assert offer is None


async def test_a_variant_of_another_product_has_no_offer(
    session: AsyncSession,
) -> None:
    first = await offered(session, "Пальто первое")
    second = await offered(session, "Пальто второе")
    variant_id = await add_variant(session, second)

    offer = await CatalogOffers(session).offer(first.id, variant_id)

    assert offer is None


async def test_many_offers_come_back_keyed_by_reference(
    session: AsyncSession,
) -> None:
    product = await offered(session, "Пальто пакетное")
    variant_id = await add_variant(session, product)

    offers = await CatalogOffers(session).offers(
        [(product.id, None), (product.id, variant_id)]
    )

    assert set(offers) == {(product.id, None), (product.id, variant_id)}


async def test_asking_for_nothing_returns_nothing(
    session: AsyncSession,
) -> None:
    assert await CatalogOffers(session).offers([]) == {}
