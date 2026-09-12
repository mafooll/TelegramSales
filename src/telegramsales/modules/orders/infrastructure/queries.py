from datetime import date
from decimal import Decimal
from typing import Any, override

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from telegramsales.modules.catalog.contracts import ProductId, VariantId
from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.orders.application.ports import (
    ICartQueries,
    IOrderQueries,
    ISelectionQueries,
)
from telegramsales.modules.orders.application.queries import (
    CartRow,
    OrderEntryView,
    OrderLineView,
    OrderView,
    SelectionRow,
)
from telegramsales.modules.orders.contracts import CartItemId, OrderId, SelectionId
from telegramsales.modules.orders.domain.enums import OrderStatus
from telegramsales.modules.orders.domain.values import OrderNumber
from telegramsales.modules.orders.infrastructure.models import (
    CartItemORM,
    OrderLineORM,
    OrderORM,
    SelectionLineORM,
    SelectionORM,
)
from telegramsales.shared.application.pagination import Page
from telegramsales.shared.domain.money import Currency, Money

LINE_COUNT = (
    select(func.count())
    .select_from(OrderLineORM)
    .where(OrderLineORM.order_id == OrderORM.id)
    .scalar_subquery()
    .label("line_count")
)


def _number(day: date, sequence: int) -> str:
    return OrderNumber(day=day, sequence=sequence).value


def _money(amount: Decimal, currency: str) -> Money:
    return Money(amount, Currency(currency))


def _variant(variant_id: int | None) -> VariantId | None:
    return None if variant_id is None else VariantId(variant_id)


async def _total[RowsType: tuple[Any, ...]](
    session: AsyncSession,
    query: Select[RowsType],
) -> int:
    counted = select(func.count()).select_from(query.subquery())
    return (await session.execute(counted)).scalar_one()


class CartQueries(ICartQueries):
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session

    @override
    async def rows_of(self, customer_id: CustomerId) -> list[CartRow]:
        query = (
            select(
                CartItemORM.id,
                CartItemORM.product_id,
                CartItemORM.variant_id,
                CartItemORM.quantity,
            )
            .where(CartItemORM.customer_id == customer_id)
            .order_by(CartItemORM.created_at, CartItemORM.id)
        )
        rows = (await self._session.execute(query)).all()
        return [
            CartRow(
                item_id=CartItemId(row.id),
                product_id=ProductId(row.product_id),
                variant_id=_variant(row.variant_id),
                quantity=row.quantity,
            )
            for row in rows
        ]

    @override
    async def count(self, customer_id: CustomerId) -> int:
        query = (
            select(func.count())
            .select_from(CartItemORM)
            .where(CartItemORM.customer_id == customer_id)
        )
        return (await self._session.execute(query)).scalar_one()


class SelectionQueries(ISelectionQueries):
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session

    @override
    async def author_of(self, selection_id: SelectionId) -> CustomerId | None:
        query = select(SelectionORM.author_id).where(SelectionORM.id == selection_id)
        found = (await self._session.execute(query)).scalar_one_or_none()
        return None if found is None else CustomerId(found)

    @override
    async def rows_of(self, selection_id: SelectionId) -> list[SelectionRow]:
        query = (
            select(
                SelectionLineORM.product_id,
                SelectionLineORM.variant_id,
                SelectionLineORM.title,
                SelectionLineORM.variant_title,
                SelectionLineORM.quantity,
            )
            .where(SelectionLineORM.selection_id == selection_id)
            .order_by(SelectionLineORM.position, SelectionLineORM.id)
        )
        rows = (await self._session.execute(query)).all()
        return [
            SelectionRow(
                product_id=ProductId(row.product_id),
                variant_id=_variant(row.variant_id),
                title=row.title,
                variant_title=row.variant_title,
                quantity=row.quantity,
            )
            for row in rows
        ]


class OrderQueries(IOrderQueries):
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session

    @override
    async def list_for(
        self,
        customer_id: CustomerId,
        number: int,
        size: int,
    ) -> Page[OrderEntryView]:
        query = (
            select(
                OrderORM.id,
                OrderORM.order_date,
                OrderORM.sequence,
                OrderORM.status,
                OrderORM.total,
                OrderORM.currency,
                OrderORM.created_at,
                LINE_COUNT,
            )
            .where(OrderORM.customer_id == customer_id)
            .order_by(OrderORM.created_at.desc())
        )
        total = await _total(self._session, query)
        rows = (
            await self._session.execute(query.limit(size).offset(number * size))
        ).all()

        return Page(
            items=[
                OrderEntryView(
                    id=OrderId(row.id),
                    number=_number(row.order_date, row.sequence),
                    status=OrderStatus(row.status),
                    total=_money(row.total, row.currency),
                    created_at=row.created_at,
                    line_count=row.line_count,
                )
                for row in rows
            ],
            number=number,
            size=size,
            total=total,
        )

    @override
    async def get_for(
        self,
        order_id: OrderId,
        customer_id: CustomerId,
    ) -> OrderView | None:
        query = select(OrderORM).where(
            OrderORM.id == order_id,
            OrderORM.customer_id == customer_id,
        )
        order = (await self._session.execute(query)).scalar_one_or_none()
        if order is None:
            return None

        lines = (
            (
                await self._session.execute(
                    select(OrderLineORM)
                    .where(OrderLineORM.order_id == order_id)
                    .order_by(OrderLineORM.position, OrderLineORM.id)
                )
            )
            .scalars()
            .all()
        )

        return OrderView(
            id=OrderId(order.id),
            number=_number(order.order_date, order.sequence),
            status=OrderStatus(order.status),
            created_at=order.created_at,
            name=order.contact_name,
            phone=order.contact_phone,
            address=order.contact_address,
            comment=order.comment,
            lines=tuple(
                OrderLineView(
                    title=line.title,
                    article=line.article,
                    variant_title=line.variant_title,
                    price=_money(line.price, line.currency),
                    old_price=(
                        None
                        if line.old_price is None
                        else _money(line.old_price, line.currency)
                    ),
                    quantity=line.quantity,
                    total=_money(line.price * line.quantity, line.currency),
                )
                for line in lines
            ),
            total=_money(order.total, order.currency),
        )
