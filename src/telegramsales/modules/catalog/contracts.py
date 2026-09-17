from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import NewType
from uuid import UUID

from telegramsales.modules.catalog.domain.enums import (
    MediaLayout as MediaLayout,  # noqa: PLC0414
)
from telegramsales.shared.domain.money import Money

CatalogId = NewType("CatalogId", int)
CategoryId = NewType("CategoryId", int)
BrandId = NewType("BrandId", int)
ProductId = NewType("ProductId", UUID)
VariantId = NewType("VariantId", int)
MediaId = NewType("MediaId", int)

type OfferKey = tuple[ProductId, VariantId | None]


@dataclass(frozen=True, slots=True)
class ProductOffer:
    product_id: ProductId
    variant_id: VariantId | None
    title: str
    article: str
    variant_title: str | None
    price: Money
    old_price: Money | None
    is_available: bool
    photo_ids: tuple[str, ...]
    media_layout: MediaLayout


class ICatalogOffers(ABC):
    @abstractmethod
    async def offer(
        self,
        product_id: ProductId,
        variant_id: VariantId | None,
    ) -> ProductOffer | None: ...

    @abstractmethod
    async def offers(
        self,
        keys: Sequence[OfferKey],
    ) -> Mapping[OfferKey, ProductOffer]: ...
