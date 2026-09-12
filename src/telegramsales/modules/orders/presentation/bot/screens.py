from telegramsales.modules.orders.application.queries import (
    CartLineView,
    CartView,
    OrderEntryView,
    OrderView,
    SelectionLineView,
    SelectionView,
)
from telegramsales.modules.orders.presentation.bot import texts
from telegramsales.modules.orders.presentation.bot.buttons import (
    ADOPT,
    ASK_CLEAR,
    CANCEL_INPUT,
    CANCEL_ORDER,
    CART_LINE_ENTRY,
    CHECKOUT,
    DROP_LINE,
    EDIT_COMMENT,
    EDIT_CONTACTS,
    ORDER_ENTRY,
    PLACE,
    SEE_ORDERS,
    SHARE,
    TAKE_LESS,
    TAKE_MORE,
    back_to_cart,
    back_to_orders,
    open_cart,
)
from telegramsales.modules.orders.presentation.bot.views import (
    CheckoutView,
    OrderListView,
    PlacedView,
    PromptView,
    cart_line_card_key,
    selection_line_key,
    status_key,
    variant_suffix,
)
from telegramsales.shared.application.i18n import ITranslator
from telegramsales.shared.presentation.bot.keyboard import ListScreen, Screen
from telegramsales.shared.presentation.bot.money import money_text
from telegramsales.shared.presentation.bot.navigation import home_button

PROMPT: Screen[PromptView] = Screen(
    content=lambda view, translate: translate(view.message_key),
    buttons=[CANCEL_INPUT],
)


def _cart_text(cart: CartView, translate: ITranslator) -> str:
    if cart.is_empty:
        return translate(texts.CART_EMPTY)
    if cart.has_unavailable:
        return translate(
            texts.CART_WITH_GONE_LINES,
            total=money_text(cart.total),
        )
    return translate(texts.CART, total=money_text(cart.total))


CART: ListScreen[CartLineView, CartView] = ListScreen(
    content=_cart_text,
    item=CART_LINE_ENTRY,
    footer=[CHECKOUT, SHARE, ASK_CLEAR, home_button()],
    footer_layout=(1, 2),
)

CART_LINE: Screen[CartLineView] = Screen(
    content=lambda line, translate: translate(
        cart_line_card_key(line),
        title=line.title,
        variant=variant_suffix(line.variant_title, translate),
        price=money_text(line.price),
        quantity=line.quantity,
        total=money_text(line.total),
    ),
    buttons=[TAKE_LESS, TAKE_MORE, DROP_LINE, back_to_cart()],
    layout=(2, 2),
)


def _confirm_text(view: CheckoutView, translate: ITranslator) -> str:
    key = texts.CONFIRM if not view.comment else texts.CONFIRM_WITH_COMMENT
    return translate(
        key,
        name=view.name,
        phone=view.phone,
        address=view.address,
        comment=view.comment,
        lines=view.lines,
        total=view.total,
    )


CHECKOUT_CONFIRM: Screen[CheckoutView] = Screen(
    content=_confirm_text,
    buttons=[PLACE, EDIT_CONTACTS, EDIT_COMMENT, back_to_cart()],
    layout=(1, 2),
)

PLACED: Screen[PlacedView] = Screen(
    content=lambda view, translate: translate(texts.PLACED, number=view.number),
    buttons=[SEE_ORDERS, home_button()],
    layout=(2,),
)

ORDER_LIST: ListScreen[OrderEntryView, OrderListView] = ListScreen(
    content=lambda view, translate: translate(
        texts.ORDER_LIST_EMPTY if view.total == 0 else texts.ORDER_LIST,
        total=view.total,
    ),
    item=ORDER_ENTRY,
    footer=[open_cart(), home_button()],
    footer_layout=(2,),
)


def _order_text(order: OrderView, translate: ITranslator) -> str:
    lines = "\n".join(
        translate(
            texts.ORDER_LINE,
            title=line.title,
            variant=variant_suffix(line.variant_title, translate),
            quantity=line.quantity,
            total=money_text(line.total),
        )
        for line in order.lines
    )
    comment = (
        ""
        if not order.comment
        else translate(texts.ORDER_COMMENT, comment=order.comment)
    )
    return translate(
        texts.ORDER_CARD,
        number=order.number,
        status=translate(status_key(order.status)),
        items=lines,
        total=money_text(order.total),
        name=order.name,
        phone=order.phone,
        address=order.address,
        comment=comment,
    )


ORDER_CARD: Screen[OrderView] = Screen(
    content=_order_text,
    buttons=[CANCEL_ORDER, back_to_orders()],
)


def _selection_text(view: SelectionView, translate: ITranslator) -> str:
    lines = "\n".join(
        translate(
            selection_line_key(line),
            title=line.title,
            variant=variant_suffix(line.variant_title, translate),
            quantity=line.quantity,
            price=_line_price(line),
        )
        for line in view.lines
    )
    return translate(texts.SELECTION, items=lines)


def _line_price(line: SelectionLineView) -> str:
    return "" if line.price is None else money_text(line.price)


SELECTION: Screen[SelectionView] = Screen(
    content=_selection_text,
    buttons=[ADOPT, open_cart(), home_button()],
    layout=(1, 2),
)
