from datetime import UTC, date, datetime
from uuid import UUID

from telegramsales.modules.catalog.contracts import ProductId, VariantId
from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.orders.contracts import (
    CartItemId,
    OrderId,
    SelectionId,
)
from telegramsales.modules.orders.domain.entities import (
    CartItem,
    Order,
    OrderLine,
    Selection,
    SelectionLine,
)
from telegramsales.modules.orders.domain.enums import OrderStatus
from telegramsales.modules.orders.domain.values import (
    Comment,
    OrderNumber,
    ProductRef,
    Quantity,
)
from telegramsales.modules.staff.contracts import StaffId
from telegramsales.shared.domain.contacts import (
    Address,
    Contacts,
    PersonName,
    Phone,
)
from telegramsales.shared.domain.money import Currency, Money

NOW = datetime(2026, 9, 12, 12, 0, tzinfo=UTC)
TODAY = date(2026, 9, 12)

BUYER = CustomerId(1000)
STRANGER = CustomerId(2000)

MANAGER = StaffId(3000)
OTHER_MANAGER = StaffId(3001)

COAT = ProductId(UUID("11111111-1111-1111-1111-111111111111"))
DRESS = ProductId(UUID("22222222-2222-2222-2222-222222222222"))
SIZE_M = VariantId(500)
SIZE_L = VariantId(501)

CART_ITEM = CartItemId(1)
ORDER = OrderId(UUID("33333333-3333-3333-3333-333333333333"))
SELECTION = SelectionId(UUID("44444444-4444-4444-4444-444444444444"))


def rub(amount: str) -> Money:
    return Money.from_external(amount, Currency.RUB)


def usd(amount: str) -> Money:
    return Money.from_external(amount, Currency.USD)


def reference(
    product_id: ProductId = COAT,
    variant_id: VariantId | None = None,
) -> ProductRef:
    return ProductRef(product_id=product_id, variant_id=variant_id)


def make_contacts(name: str = "Иван Петров") -> Contacts:
    return Contacts(
        name=PersonName(name),
        phone=Phone("+79991234567"),
        address=Address("Москва, Тверская 1"),
    )


def make_cart_item(
    item_id: CartItemId = CART_ITEM,
    *,
    customer_id: CustomerId = BUYER,
    product_id: ProductId = COAT,
    variant_id: VariantId | None = None,
    quantity: int = 1,
) -> CartItem:
    return CartItem.create(
        item_id=item_id,
        customer_id=customer_id,
        reference=reference(product_id, variant_id),
        quantity=Quantity(quantity),
        now=NOW,
    )


def make_order_line(  # noqa: PLR0913
    title: str = "Пальто оверсайз",
    *,
    price: str = "12900",
    old_price: str | None = None,
    quantity: int = 1,
    variant_title: str | None = None,
    product_id: ProductId = COAT,
) -> OrderLine:
    return OrderLine(
        reference=reference(product_id),
        title=title,
        article="000042",
        variant_title=variant_title,
        price=rub(price),
        old_price=None if old_price is None else rub(old_price),
        quantity=Quantity(quantity),
    )


def make_order(
    *,
    lines: tuple[OrderLine, ...] = (),
    customer_id: CustomerId = BUYER,
    comment: str = "",
    sequence: int = 1,
) -> Order:
    return Order.place(
        order_id=ORDER,
        number=OrderNumber(day=TODAY, sequence=sequence),
        customer_id=customer_id,
        contacts=make_contacts(),
        comment=Comment(comment),
        lines=lines or (make_order_line(),),
        now=NOW,
    )


def make_taken_order(
    status: OrderStatus = OrderStatus.IN_WORK,
    *,
    manager_id: StaffId = MANAGER,
) -> Order:
    order = make_order()
    order.take_in_work(manager_id)
    order.status = status
    _ = order.collect_events()
    return order


def make_selection_line(
    title: str = "Пальто оверсайз",
    *,
    product_id: ProductId = COAT,
    variant_id: VariantId | None = None,
    variant_title: str | None = None,
    quantity: int = 1,
) -> SelectionLine:
    return SelectionLine(
        reference=reference(product_id, variant_id),
        title=title,
        variant_title=variant_title,
        quantity=Quantity(quantity),
    )


def make_selection(
    *,
    author_id: CustomerId = BUYER,
    lines: tuple[SelectionLine, ...] = (),
) -> Selection:
    return Selection.create(
        selection_id=SELECTION,
        author_id=author_id,
        lines=lines or (make_selection_line(),),
        now=NOW,
    )
