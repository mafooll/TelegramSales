from aiogram.enums import ButtonStyle

from telegramsales.modules.orders.application.queries import (
    CartLineView,
    CartView,
    OrderEntryView,
    OrderView,
    SelectionView,
)
from telegramsales.modules.orders.presentation.bot import texts
from telegramsales.modules.orders.presentation.bot.callbacks import (
    CartAction,
    CartCallback,
    OrderAction,
    OrderCallback,
    SelectionAction,
    SelectionCallback,
)
from telegramsales.modules.orders.presentation.bot.views import (
    CheckoutView,
    PlacedView,
    PromptView,
    can_add_more,
    can_take_away,
    cart_line_key,
    status_key,
    variant_suffix,
)
from telegramsales.shared.presentation.bot.keyboard import Button, label
from telegramsales.shared.presentation.bot.money import money_text


def open_cart[ViewType]() -> Button[ViewType]:
    return Button(
        text=label(texts.OPEN_CART_BUTTON),
        callback=lambda _: CartCallback(action=CartAction.OPEN),
    )


def open_orders[ViewType]() -> Button[ViewType]:
    return Button(
        text=label(texts.OPEN_ORDERS_BUTTON),
        callback=lambda _: OrderCallback(action=OrderAction.LIST),
    )


def back_to_cart[ViewType]() -> Button[ViewType]:
    return Button(
        text=label(texts.BACK_BUTTON),
        callback=lambda _: CartCallback(action=CartAction.OPEN),
    )


CANCEL_INPUT: Button[PromptView] = Button(
    text=label(texts.BACK_BUTTON),
    callback=lambda view: view.back,
)

CART_LINE_ENTRY: Button[CartLineView] = Button(
    text=lambda line, translate: translate(
        cart_line_key(line),
        title=line.title,
        variant=variant_suffix(line.variant_title, translate),
        quantity=line.quantity,
        total=money_text(line.total),
    ),
    callback=lambda line: CartCallback(
        action=CartAction.LINE,
        item_id=line.item_id,
    ),
)

CHECKOUT: Button[CartView] = Button(
    text=label(texts.CHECKOUT_BUTTON),
    callback=lambda _: CartCallback(action=CartAction.CHECKOUT),
    when=lambda cart: not cart.is_empty and not cart.has_unavailable,
    style=ButtonStyle.PRIMARY,
)

SHARE: Button[CartView] = Button(
    text=label(texts.SHARE_BUTTON),
    callback=lambda _: CartCallback(action=CartAction.SHARE),
    when=lambda cart: not cart.is_empty,
)

ASK_CLEAR: Button[CartView] = Button(
    text=label(texts.CLEAR_BUTTON),
    callback=lambda _: CartCallback(action=CartAction.ASK_CLEAR),
    when=lambda cart: not cart.is_empty,
    style=ButtonStyle.DANGER,
)

TAKE_MORE: Button[CartLineView] = Button(
    text=label(texts.MORE_BUTTON),
    callback=lambda line: CartCallback(
        action=CartAction.MORE,
        item_id=line.item_id,
    ),
    when=can_add_more,
)

TAKE_LESS: Button[CartLineView] = Button(
    text=label(texts.LESS_BUTTON),
    callback=lambda line: CartCallback(
        action=CartAction.LESS,
        item_id=line.item_id,
    ),
    when=can_take_away,
)

DROP_LINE: Button[CartLineView] = Button(
    text=label(texts.DROP_BUTTON),
    callback=lambda line: CartCallback(
        action=CartAction.DROP,
        item_id=line.item_id,
    ),
    style=ButtonStyle.DANGER,
)

PLACE: Button[CheckoutView] = Button(
    text=label(texts.PLACE_BUTTON),
    callback=lambda _: CartCallback(action=CartAction.PLACE),
    style=ButtonStyle.SUCCESS,
)

EDIT_CONTACTS: Button[CheckoutView] = Button(
    text=label(texts.CONTACTS_BUTTON),
    callback=lambda _: CartCallback(action=CartAction.CONTACTS),
)

EDIT_COMMENT: Button[CheckoutView] = Button(
    text=label(texts.COMMENT_BUTTON),
    callback=lambda _: CartCallback(action=CartAction.COMMENT),
)

ORDER_ENTRY: Button[OrderEntryView] = Button(
    text=lambda order, translate: translate(
        texts.ORDER_ENTRY,
        number=order.number,
        status=translate(status_key(order.status)),
        total=money_text(order.total),
    ),
    callback=lambda order: OrderCallback(
        action=OrderAction.CARD,
        order_id=order.id,
    ),
)

CANCEL_ORDER: Button[OrderView] = Button(
    text=label(texts.CANCEL_ORDER_BUTTON),
    callback=lambda order: OrderCallback(
        action=OrderAction.ASK_CANCEL,
        order_id=order.id,
    ),
    when=lambda order: order.is_open,
    style=ButtonStyle.DANGER,
)


def back_to_orders[ViewType]() -> Button[ViewType]:
    return Button(
        text=label(texts.BACK_BUTTON),
        callback=lambda _: OrderCallback(action=OrderAction.LIST),
    )


ADOPT: Button[SelectionView] = Button(
    text=label(texts.ADOPT_BUTTON),
    callback=lambda selection: SelectionCallback(
        action=SelectionAction.ADOPT,
        selection_id=selection.id,
    ),
    when=lambda selection: selection.available_count > 0,
    style=ButtonStyle.PRIMARY,
)

SEE_ORDERS: Button[PlacedView] = Button(
    text=label(texts.OPEN_ORDERS_BUTTON),
    callback=lambda _: OrderCallback(action=OrderAction.LIST),
    style=ButtonStyle.PRIMARY,
)
