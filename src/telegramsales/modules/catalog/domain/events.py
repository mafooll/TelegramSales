from dataclasses import dataclass

from telegramsales.modules.catalog.contracts import CatalogId, ProductId
from telegramsales.shared.domain.event import DomainEvent


@dataclass(frozen=True, kw_only=True)
class ProductPublished(DomainEvent):
    product_id: ProductId
    catalog_id: CatalogId
    title: str
    article: str
