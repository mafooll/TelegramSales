from dataclasses import dataclass
from datetime import datetime

from telegramsales.modules.catalog.contracts import MediaLayout, ProductId, VariantId
from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.orders.contracts import (
    CartItemId,
    OrderId,
    SelectionId,
)
from telegramsales.modules.orders.domain.enums import OrderStatus
from telegramsales.shared.domain.money import Money


@dataclass(frozen=True, slots=True)
class CartRow:
    item_id: CartItemId
    product_id: ProductId
    variant_id: VariantId | None
    quantity: int


@dataclass(frozen=True, slots=True)
class SelectionRow:
    product_id: ProductId
    variant_id: VariantId | None
    title: str
    variant_title: str | None
    quantity: int


@dataclass(frozen=True, slots=True)
class CartLineView:
    item_id: CartItemId
    title: str
    variant_title: str | None
    price: Money
    quantity: int
    total: Money
    is_available: bool
    photo_ids: tuple[str, ...]
    media_layout: MediaLayout


@dataclass(frozen=True, slots=True)
class CartView:
    lines: tuple[CartLineView, ...]
    total: Money

    @property
    def is_empty(self) -> bool:
        return not self.lines

    @property
    def has_unavailable(self) -> bool:
        return any(not line.is_available for line in self.lines)


@dataclass(frozen=True, slots=True)
class SelectionLineView:
    title: str
    variant_title: str | None
    price: Money | None
    quantity: int
    is_available: bool


@dataclass(frozen=True, slots=True)
class SelectionView:
    id: SelectionId
    author_id: CustomerId
    lines: tuple[SelectionLineView, ...]

    @property
    def available_count(self) -> int:
        return sum(1 for line in self.lines if line.is_available)

    @property
    def has_unavailable(self) -> bool:
        return any(not line.is_available for line in self.lines)


@dataclass(frozen=True, slots=True)
class OrderEntryView:
    id: OrderId
    number: str
    status: OrderStatus
    total: Money
    created_at: datetime
    line_count: int


@dataclass(frozen=True, slots=True)
class OrderLineView:
    title: str
    article: str
    variant_title: str | None
    price: Money
    old_price: Money | None
    quantity: int
    total: Money


@dataclass(frozen=True, slots=True)
class OrderView:
    id: OrderId
    number: str
    status: OrderStatus
    created_at: datetime
    name: str
    phone: str
    address: str
    comment: str
    lines: tuple[OrderLineView, ...]
    total: Money

    @property
    def is_open(self) -> bool:
        return self.status is OrderStatus.PLACED
