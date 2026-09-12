from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from telegramsales.modules.catalog.contracts import ProductId, VariantId
from telegramsales.modules.catalog.domain.entities import Product, ProductVariant
from telegramsales.modules.catalog.domain.values import Title
from telegramsales.modules.catalog.infrastructure.repositories import (
    ProductRepository,
    ProductVariantRepository,
)
from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.customers.domain.entities import Customer
from telegramsales.modules.customers.domain.values import DisplayName
from telegramsales.modules.customers.infrastructure.repositories import (
    CustomerRepository,
)
from telegramsales.modules.orders.contracts import SelectionId
from telegramsales.modules.orders.domain.entities import (
    CartItem,
    Order,
    OrderLine,
    Selection,
)
from telegramsales.modules.orders.domain.values import (
    Comment,
    OrderNumber,
    ProductRef,
    Quantity,
)
from telegramsales.modules.orders.infrastructure.queries import (
    CartQueries,
    OrderQueries,
    SelectionQueries,
)
from telegramsales.modules.orders.infrastructure.repositories import (
    CartRepository,
    OrderRepository,
    SelectionRepository,
)
from tests.catalog.test_product_persistence import store_product
from tests.orders.factories import (
    NOW,
    TODAY,
    make_contacts,
    make_selection_line,
    rub,
)

pytestmark = pytest.mark.db

PAGE_SIZE = 8
BUYER = CustomerId(70001)
FRIEND = CustomerId(70002)


async def store_customer(
    session: AsyncSession,
    customer_id: CustomerId = BUYER,
    name: str = "Иван Петров",
) -> Customer:
    repository = CustomerRepository(session)
    customer = Customer.create(
        customer_id=customer_id,
        name=DisplayName(name),
        now=NOW,
    )
    await repository.add(customer)
    return customer


async def store_variant(
    session: AsyncSession,
    product: Product,
    title: str = "M",
) -> VariantId:
    repository = ProductVariantRepository(session)
    variant = ProductVariant.create(
        variant_id=await repository.next_id(),
        product_id=product.id,
        title=Title(title),
        price_override=None,
    )
    await repository.add(variant)
    return variant.id


async def put_in_cart(
    session: AsyncSession,
    product: Product,
    *,
    customer_id: CustomerId = BUYER,
    variant_id: VariantId | None = None,
    quantity: int = 1,
) -> CartItem:
    repository = CartRepository(session)
    item = CartItem.create(
        item_id=await repository.next_id(),
        customer_id=customer_id,
        reference=ProductRef(product_id=product.id, variant_id=variant_id),
        quantity=Quantity(quantity),
        now=NOW,
    )
    await repository.add(item)
    return item


async def test_a_cart_line_survives_a_round_trip(session: AsyncSession) -> None:
    await store_customer(session)
    product = await store_product(session, "Пальто корзинное")
    stored = await put_in_cart(session, product, quantity=3)

    loaded = await CartRepository(session).get(stored.id)

    assert loaded is not None
    assert loaded.quantity == Quantity(3)
    assert loaded.reference.product_id == product.id


async def test_a_line_without_a_variant_is_found(session: AsyncSession) -> None:
    await store_customer(session)
    product = await store_product(session, "Пальто без размера")
    await put_in_cart(session, product)

    found = await CartRepository(session).find(
        BUYER, ProductRef(product_id=product.id)
    )

    assert found is not None


async def test_a_line_with_a_variant_is_found(session: AsyncSession) -> None:
    await store_customer(session)
    product = await store_product(session, "Пальто с размером")
    variant_id = await store_variant(session, product)
    await put_in_cart(session, product, variant_id=variant_id)

    found = await CartRepository(session).find(
        BUYER, ProductRef(product_id=product.id, variant_id=variant_id)
    )

    assert found is not None


async def test_the_variant_line_is_not_the_plain_line(
    session: AsyncSession,
) -> None:
    await store_customer(session)
    product = await store_product(session, "Пальто обе строки")
    variant_id = await store_variant(session, product)
    await put_in_cart(session, product, variant_id=variant_id)

    found = await CartRepository(session).find(
        BUYER, ProductRef(product_id=product.id)
    )

    assert found is None


async def test_the_same_line_cannot_be_stored_twice(
    session: AsyncSession,
) -> None:
    await store_customer(session)
    product = await store_product(session, "Пальто дважды")
    await put_in_cart(session, product)

    with pytest.raises(IntegrityError):
        await put_in_cart(session, product)


async def test_two_customers_keep_separate_carts(session: AsyncSession) -> None:
    await store_customer(session)
    await store_customer(session, FRIEND, "Пётр")
    product = await store_product(session, "Пальто на двоих")
    await put_in_cart(session, product)
    await put_in_cart(session, product, customer_id=FRIEND)

    mine = await CartRepository(session).items_of(BUYER)

    assert [item.customer_id for item in mine] == [BUYER]


async def test_clearing_leaves_the_other_cart_alone(
    session: AsyncSession,
) -> None:
    await store_customer(session)
    await store_customer(session, FRIEND, "Пётр")
    product = await store_product(session, "Пальто очистки")
    await put_in_cart(session, product)
    await put_in_cart(session, product, customer_id=FRIEND)
    repository = CartRepository(session)

    await repository.clear(BUYER)

    assert await repository.items_of(BUYER) == []
    assert len(await repository.items_of(FRIEND)) == 1


async def test_deleting_a_product_empties_the_line(
    session: AsyncSession,
) -> None:
    await store_customer(session)
    product = await store_product(session, "Пальто на удаление")
    await put_in_cart(session, product)

    await ProductRepository(session).delete(product)

    assert await CartRepository(session).items_of(BUYER) == []


async def test_cart_rows_come_out_for_reading(session: AsyncSession) -> None:
    await store_customer(session)
    product = await store_product(session, "Пальто чтения")
    await put_in_cart(session, product, quantity=2)

    rows = await CartQueries(session).rows_of(BUYER)

    assert [(row.product_id, row.quantity) for row in rows] == [(product.id, 2)]


async def make_order(
    session: AsyncSession,
    *,
    customer_id: CustomerId = BUYER,
    sequence: int = 1,
    day: date = TODAY,
    comment: str = "",
) -> Order:
    repository = OrderRepository(session)
    order = Order.place(
        order_id=await repository.next_id(),
        number=OrderNumber(day=day, sequence=sequence),
        customer_id=customer_id,
        contacts=make_contacts(),
        comment=Comment(comment),
        lines=(
            OrderLine(
                reference=ProductRef(product_id=_any_product_id()),
                title="Пальто оверсайз",
                article="000042",
                variant_title="M",
                price=rub("12900"),
                old_price=rub("15900"),
                quantity=Quantity(2),
            ),
        ),
        now=NOW,
    )
    await repository.add(order)
    return order


def _any_product_id() -> ProductId:
    return ProductId(uuid4())


async def test_an_order_survives_a_round_trip(session: AsyncSession) -> None:
    await store_customer(session)
    stored = await make_order(session, comment="позвоните заранее")

    loaded = await OrderRepository(session).get(stored.id)

    assert loaded is not None
    assert loaded.number.value == stored.number.value
    assert loaded.total == rub("25800")
    assert loaded.comment == Comment("позвоните заранее")
    assert loaded.contacts.phone.value == "+79991234567"
    assert loaded.lines[0].old_price == rub("15900")


async def test_the_day_counter_starts_at_one(session: AsyncSession) -> None:
    assert await OrderRepository(session).next_sequence(TODAY) == 1


async def test_the_day_counter_counts_on(session: AsyncSession) -> None:
    await store_customer(session)
    await make_order(session, sequence=4)

    assert await OrderRepository(session).next_sequence(TODAY) == 5


async def test_the_counter_starts_over_the_next_day(
    session: AsyncSession,
) -> None:
    await store_customer(session)
    await make_order(session, sequence=4)

    assert await OrderRepository(session).next_sequence(date(2026, 9, 13)) == 1


async def test_two_orders_cannot_share_a_number(session: AsyncSession) -> None:
    await store_customer(session)
    await make_order(session, sequence=1)

    with pytest.raises(IntegrityError):
        await make_order(session, sequence=1)


async def test_an_order_is_listed_for_its_owner(session: AsyncSession) -> None:
    await store_customer(session)
    stored = await make_order(session)

    page = await OrderQueries(session).list_for(BUYER, 0, PAGE_SIZE)

    assert [entry.id for entry in page.items] == [stored.id]
    assert page.items[0].line_count == 1


async def test_an_order_is_not_listed_for_a_stranger(
    session: AsyncSession,
) -> None:
    await store_customer(session)
    await store_customer(session, FRIEND, "Пётр")
    await make_order(session)

    page = await OrderQueries(session).list_for(FRIEND, 0, PAGE_SIZE)

    assert page.items == []


async def test_an_order_card_reads_its_lines(session: AsyncSession) -> None:
    await store_customer(session)
    stored = await make_order(session)

    view = await OrderQueries(session).get_for(stored.id, BUYER)

    assert view is not None
    assert view.lines[0].total == rub("25800")
    assert view.name == "Иван Петров"


async def test_a_stranger_cannot_read_the_card(session: AsyncSession) -> None:
    await store_customer(session)
    await store_customer(session, FRIEND, "Пётр")
    stored = await make_order(session)

    assert await OrderQueries(session).get_for(stored.id, FRIEND) is None


async def test_a_selection_survives_a_round_trip(session: AsyncSession) -> None:
    await store_customer(session)
    repository = SelectionRepository(session)
    stored = Selection.create(
        selection_id=await repository.next_id(),
        author_id=BUYER,
        lines=(
            make_selection_line(quantity=2),
            make_selection_line("Платье", variant_title="M"),
        ),
        now=NOW,
    )
    await repository.add(stored)

    loaded = await repository.get(stored.id)

    assert loaded is not None
    assert [line.title for line in loaded.lines] == [
        "Пальто оверсайз",
        "Платье",
    ]
    assert loaded.lines[0].quantity == Quantity(2)
    assert loaded.lines[1].variant_title == "M"


async def test_selection_rows_come_out_for_reading(
    session: AsyncSession,
) -> None:
    await store_customer(session)
    repository = SelectionRepository(session)
    stored = Selection.create(
        selection_id=await repository.next_id(),
        author_id=BUYER,
        lines=(make_selection_line(),),
        now=NOW,
    )
    await repository.add(stored)

    queries = SelectionQueries(session)

    assert await queries.author_of(stored.id) == BUYER
    assert [row.title for row in await queries.rows_of(stored.id)] == [
        "Пальто оверсайз"
    ]


async def test_an_unknown_selection_has_no_author(
    session: AsyncSession,
) -> None:
    found = await SelectionQueries(session).author_of(SelectionId(uuid4()))

    assert found is None
