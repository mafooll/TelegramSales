from datetime import date
from typing import override
from uuid import uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.orders.application.ports import (
    ICartRepository,
    IOrderRepository,
    ISelectionRepository,
)
from telegramsales.modules.orders.contracts import (
    CartItemId,
    OrderId,
    SelectionId,
)
from telegramsales.modules.orders.domain.entities import (
    CartItem,
    Order,
    Selection,
)
from telegramsales.modules.orders.domain.values import ProductRef
from telegramsales.modules.orders.infrastructure.filters import variant_filter
from telegramsales.modules.orders.infrastructure.mappers import (
    CartItemMapper,
    order_line_to_model,
    order_to_entity,
    order_to_model,
    selection_line_to_model,
    selection_to_entity,
    selection_to_model,
)
from telegramsales.modules.orders.infrastructure.models import (
    CartItemORM,
    OrderLineORM,
    OrderORM,
    SelectionLineORM,
    SelectionORM,
)
from telegramsales.shared.infrastructure.database.repository import Repository

ID_COLUMN = "id"
FIRST_SEQUENCE = 1


async def _next_id(session: AsyncSession, table: str) -> int:
    sequence = func.pg_get_serial_sequence(table, ID_COLUMN)
    return (await session.execute(select(func.nextval(sequence)))).scalar_one()


class CartRepository(ICartRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session
        self._models: Repository[CartItemORM, int] = Repository(session, CartItemORM)

    @override
    async def next_id(self) -> CartItemId:
        return CartItemId(await _next_id(self._session, CartItemORM.__tablename__))

    @override
    async def get(self, item_id: CartItemId) -> CartItem | None:
        model = await self._models.get(item_id)
        return CartItemMapper.to_entity(model) if model is not None else None

    @override
    async def find(
        self,
        customer_id: CustomerId,
        reference: ProductRef,
    ) -> CartItem | None:
        query = select(CartItemORM).where(
            CartItemORM.customer_id == customer_id,
            CartItemORM.product_id == reference.product_id,
            variant_filter(reference.variant_id),
        )
        model = (await self._session.execute(query)).scalar_one_or_none()
        return CartItemMapper.to_entity(model) if model is not None else None

    @override
    async def items_of(self, customer_id: CustomerId) -> list[CartItem]:
        query = (
            select(CartItemORM)
            .where(CartItemORM.customer_id == customer_id)
            .order_by(CartItemORM.created_at, CartItemORM.id)
        )
        models = (await self._session.execute(query)).scalars().all()
        return [CartItemMapper.to_entity(model) for model in models]

    @override
    async def add(self, item: CartItem) -> None:
        await self._models.add(CartItemMapper.to_model(item))

    @override
    async def save(self, item: CartItem) -> None:
        await self._models.merge(CartItemMapper.to_model(item))

    @override
    async def delete(self, item: CartItem) -> None:
        model = await self._models.get(item.id)
        if model is not None:
            await self._models.delete(model)

    @override
    async def clear(self, customer_id: CustomerId) -> None:
        await self._session.execute(
            delete(CartItemORM).where(CartItemORM.customer_id == customer_id)
        )
        await self._session.flush()


class SelectionRepository(ISelectionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session
        self._models: Repository[SelectionORM, SelectionId] = Repository(
            session, SelectionORM
        )

    @override
    async def next_id(self) -> SelectionId:
        return SelectionId(uuid4())

    @override
    async def get(self, selection_id: SelectionId) -> Selection | None:
        model = await self._models.get(selection_id)
        if model is None:
            return None

        query = (
            select(SelectionLineORM)
            .where(SelectionLineORM.selection_id == selection_id)
            .order_by(SelectionLineORM.position, SelectionLineORM.id)
        )
        lines = list((await self._session.execute(query)).scalars().all())
        return selection_to_entity(model, lines)

    @override
    async def add(self, selection: Selection) -> None:
        await self._models.add(selection_to_model(selection))
        for position, line in enumerate(selection.lines):
            self._session.add(selection_line_to_model(selection.id, line, position))
        await self._session.flush()


class OrderRepository(IOrderRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session
        self._models: Repository[OrderORM, OrderId] = Repository(session, OrderORM)

    @override
    async def next_id(self) -> OrderId:
        return OrderId(uuid4())

    @override
    async def next_sequence(self, day: date) -> int:
        query = select(func.max(OrderORM.sequence)).where(OrderORM.order_date == day)
        highest = (await self._session.execute(query)).scalar_one_or_none()
        return FIRST_SEQUENCE if highest is None else highest + FIRST_SEQUENCE

    @override
    async def get(self, order_id: OrderId) -> Order | None:
        model = await self._models.get(order_id)
        if model is None:
            return None

        query = (
            select(OrderLineORM)
            .where(OrderLineORM.order_id == order_id)
            .order_by(OrderLineORM.position, OrderLineORM.id)
        )
        lines = list((await self._session.execute(query)).scalars().all())
        return order_to_entity(model, lines)

    @override
    async def add(self, order: Order) -> None:
        await self._models.add(order_to_model(order))
        for position, line in enumerate(order.lines):
            self._session.add(order_line_to_model(order.id, line, position))
        await self._session.flush()

    @override
    async def save(self, order: Order) -> None:
        await self._models.merge(order_to_model(order))
