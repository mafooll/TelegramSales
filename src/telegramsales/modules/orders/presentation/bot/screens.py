from aiogram.types import InputRichBlockUnion

from telegramsales.modules.catalog.contracts import MediaLayout
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
    cart_line_caption,
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
from telegramsales.shared.presentation.bot.content import (
    Content,
    bold,
    code,
    divider,
    gallery,
    heading,
    paragraph,
    parts,
    slideshow,
)
from telegramsales.shared.presentation.bot.keyboard import ListScreen, Screen
from telegramsales.shared.presentation.bot.money import money_text
from telegramsales.shared.presentation.bot.navigation import home_button

PROMPT: Screen[PromptView] = Screen(
    content=lambda view, translate: translate(view.message_key),
    buttons=[CANCEL_INPUT],
)


def _cart_text(cart: CartView, translate: ITranslator) -> Content:
    if cart.is_empty:
        return translate(texts.CART_EMPTY)

    blocks: list[InputRichBlockUnion] = [
        heading(translate(texts.CART)),
        parts(translate(texts.CART_TOTAL), " ", bold(money_text(cart.total))),
    ]
    if cart.has_unavailable:
        blocks.append(paragraph(translate(texts.CART_WITH_GONE_LINES)))
    blocks.append(divider())
    return blocks


def _cart_line_thumbnail(line: CartLineView) -> str | None:
    return line.photo_ids[0] if line.photo_ids else None


CART: ListScreen[CartLineView, CartView] = ListScreen(
    content=_cart_text,
    item=CART_LINE_ENTRY,
    item_photo=_cart_line_thumbnail,
    item_caption=cart_line_caption,
    footer=[CHECKOUT, SHARE, ASK_CLEAR, home_button()],
    footer_layout=(1, 2),
)


def _cart_line_photos(line: CartLineView) -> list[InputRichBlockUnion]:
    if line.media_layout is MediaLayout.SLIDESHOW:
        return slideshow(line.photo_ids)
    return gallery(line.photo_ids)


def _cart_line_content(line: CartLineView, translate: ITranslator) -> Content:
    text = translate(
        cart_line_card_key(line),
        title=line.title,
        variant=variant_suffix(line.variant_title, translate),
        price=money_text(line.price),
        quantity=line.quantity,
        total=money_text(line.total),
    )
    return [paragraph(text), *_cart_line_photos(line)]


CART_LINE: Screen[CartLineView] = Screen(
    content=_cart_line_content,
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


def _order_text(order: OrderView, translate: ITranslator) -> Content:
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
    return [
        parts(translate(texts.ORDER_NUMBER), " ", code(order.number)),
        parts(
            translate(texts.ORDER_STATUS),
            " ",
            bold(translate(status_key(order.status))),
        ),
        divider(),
        paragraph(lines),
        parts(translate(texts.ORDER_TOTAL), " ", bold(money_text(order.total))),
        divider(),
        paragraph(
            translate(
                texts.ORDER_CONTACTS,
                name=order.name,
                phone=order.phone,
                address=order.address,
                comment=comment,
            )
        ),
    ]


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
