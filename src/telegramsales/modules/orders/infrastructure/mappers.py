from decimal import Decimal
from typing import override

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
from telegramsales.modules.orders.infrastructure.models import (
    CartItemORM,
    OrderLineORM,
    OrderORM,
    SelectionLineORM,
    SelectionORM,
)
from telegramsales.modules.staff.contracts import StaffId
from telegramsales.shared.domain.contacts import (
    Address,
    Contacts,
    PersonName,
    Phone,
)
from telegramsales.shared.domain.money import Currency, Money
from telegramsales.shared.infrastructure.database.mapper import IEntityMapper


def _money(amount: Decimal, currency: str) -> Money:
    return Money(amount, Currency(currency))


def _reference(product_id: object, variant_id: int | None) -> ProductRef:
    return ProductRef(
        product_id=ProductId(product_id),  # pyright: ignore[reportArgumentType]
        variant_id=None if variant_id is None else VariantId(variant_id),
    )


class CartItemMapper(IEntityMapper[CartItem, CartItemORM]):
    @staticmethod
    @override
    def to_entity(model: CartItemORM) -> CartItem:
        return CartItem(
            id=CartItemId(model.id),
            customer_id=CustomerId(model.customer_id),
            reference=_reference(model.product_id, model.variant_id),
            quantity=Quantity(model.quantity),
            added_at=model.created_at,
        )

    @staticmethod
    @override
    def to_model(entity: CartItem) -> CartItemORM:
        return CartItemORM(
            id=entity.id,
            customer_id=entity.customer_id,
            product_id=entity.reference.product_id,
            variant_id=entity.reference.variant_id,
            quantity=entity.quantity.value,
            created_at=entity.added_at,
        )


def selection_line_to_model(
    selection_id: SelectionId,
    line: SelectionLine,
    position: int,
) -> SelectionLineORM:
    return SelectionLineORM(
        selection_id=selection_id,
        product_id=line.reference.product_id,
        variant_id=line.reference.variant_id,
        title=line.title,
        variant_title=line.variant_title,
        quantity=line.quantity.value,
        position=position,
    )


def selection_to_entity(
    model: SelectionORM,
    lines: list[SelectionLineORM],
) -> Selection:
    return Selection(
        id=SelectionId(model.id),
        author_id=CustomerId(model.author_id),
        created_at=model.created_at,
        lines=tuple(
            SelectionLine(
                reference=_reference(line.product_id, line.variant_id),
                title=line.title,
                variant_title=line.variant_title,
                quantity=Quantity(line.quantity),
            )
            for line in lines
        ),
    )


def selection_to_model(entity: Selection) -> SelectionORM:
    return SelectionORM(
        id=entity.id,
        author_id=entity.author_id,
        created_at=entity.created_at,
    )


def order_line_to_model(
    order_id: OrderId,
    line: OrderLine,
    position: int,
) -> OrderLineORM:
    return OrderLineORM(
        order_id=order_id,
        product_id=line.reference.product_id,
        variant_id=line.reference.variant_id,
        title=line.title,
        article=line.article,
        variant_title=line.variant_title,
        price=line.price.amount,
        old_price=None if line.old_price is None else line.old_price.amount,
        currency=line.price.currency.value,
        quantity=line.quantity.value,
        position=position,
    )


def order_to_entity(model: OrderORM, lines: list[OrderLineORM]) -> Order:
    return Order(
        id=OrderId(model.id),
        number=OrderNumber(day=model.order_date, sequence=model.sequence),
        customer_id=CustomerId(model.customer_id),
        contacts=Contacts(
            name=PersonName(model.contact_name),
            phone=Phone(model.contact_phone),
            address=Address(model.contact_address),
        ),
        comment=Comment(model.comment),
        created_at=model.created_at,
        status=OrderStatus(model.status),
        manager_id=None if model.manager_id is None else StaffId(model.manager_id),
        lines=tuple(
            OrderLine(
                reference=_reference(line.product_id, line.variant_id),
                title=line.title,
                article=line.article,
                variant_title=line.variant_title,
                price=_money(line.price, line.currency),
                old_price=(
                    None
                    if line.old_price is None
                    else _money(line.old_price, line.currency)
                ),
                quantity=Quantity(line.quantity),
            )
            for line in lines
        ),
    )


def order_to_model(entity: Order) -> OrderORM:
    return OrderORM(
        id=entity.id,
        customer_id=entity.customer_id,
        manager_id=entity.manager_id,
        order_date=entity.number.day,
        sequence=entity.number.sequence,
        status=entity.status.value,
        contact_name=entity.contacts.name.value,
        contact_phone=entity.contacts.phone.value,
        contact_address=entity.contacts.address.value,
        comment=entity.comment.value,
        total=entity.total.amount,
        currency=entity.total.currency.value,
        created_at=entity.created_at,
    )
