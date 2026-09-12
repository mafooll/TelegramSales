from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any, final, override

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from telegramsales.modules.catalog.contracts import (
    ICatalogOffers,
    OfferKey,
    ProductId,
    ProductOffer,
    VariantId,
)
from telegramsales.modules.catalog.infrastructure.models import (
    ProductORM,
    ProductVariantORM,
)
from telegramsales.shared.domain.money import Currency, Money


def _money(amount: Decimal, currency: str) -> Money:
    return Money(amount, Currency(currency))


@final
class CatalogOffers(ICatalogOffers):
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session

    @override
    async def offer(
        self,
        product_id: ProductId,
        variant_id: VariantId | None,
    ) -> ProductOffer | None:
        found = await self.offers([(product_id, variant_id)])
        return found.get((product_id, variant_id))

    @override
    async def offers(
        self,
        keys: Sequence[OfferKey],
    ) -> Mapping[OfferKey, ProductOffer]:
        if not keys:
            return {}

        product_ids = {product_id for product_id, _ in keys}
        products = await self._products(product_ids)
        variants = await self._variants(product_ids)

        offers: dict[OfferKey, ProductOffer] = {}
        for key in keys:
            product_id, variant_id = key
            product = products.get(product_id)
            if product is None:
                continue
            variant = None if variant_id is None else variants.get(variant_id)
            if variant_id is not None and variant is None:
                continue
            if variant is not None and variant.product_id != product_id:
                continue
            offers[key] = _to_offer(product, variant)
        return offers

    async def _products(
        self,
        product_ids: set[ProductId],
    ) -> dict[ProductId, Any]:
        query = select(
            ProductORM.id,
            ProductORM.article,
            ProductORM.title,
            ProductORM.price,
            ProductORM.old_price,
            ProductORM.currency,
            ProductORM.published_at,
            ProductORM.is_visible,
            ProductORM.is_in_stock,
        ).where(ProductORM.id.in_(product_ids))
        rows = (await self._session.execute(query)).all()
        return {ProductId(row.id): row for row in rows}

    async def _variants(
        self,
        product_ids: set[ProductId],
    ) -> dict[VariantId, Any]:
        query = select(
            ProductVariantORM.id,
            ProductVariantORM.product_id,
            ProductVariantORM.title,
            ProductVariantORM.price_override,
            ProductVariantORM.is_available,
        ).where(ProductVariantORM.product_id.in_(product_ids))
        rows = (await self._session.execute(query)).all()
        return {VariantId(row.id): row for row in rows}


def _to_offer(product: Any, variant: Any) -> ProductOffer:  # noqa: ANN401
    override = None if variant is None else variant.price_override
    price = product.price if override is None else override
    offered = (
        product.published_at is not None
        and product.is_visible
        and product.is_in_stock
        and (variant is None or variant.is_available)
    )
    return ProductOffer(
        product_id=ProductId(product.id),
        variant_id=None if variant is None else VariantId(variant.id),
        title=product.title,
        article=product.article,
        variant_title=None if variant is None else variant.title,
        price=_money(price, product.currency),
        old_price=(
            None
            if product.old_price is None
            else _money(product.old_price, product.currency)
        ),
        is_available=offered,
    )
