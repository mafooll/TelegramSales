from telegramsales.modules.desk.presentation.bot import texts
from telegramsales.modules.desk.presentation.bot.buttons import (
    CANCEL,
    DONE,
    PAID,
    SHIPPED,
    TAKE,
)
from telegramsales.modules.desk.presentation.bot.views import (
    status_key,
    variant_suffix,
)
from telegramsales.modules.orders.contracts import OrderCardView
from telegramsales.shared.application.i18n import ITranslator
from telegramsales.shared.presentation.bot.keyboard import Screen
from telegramsales.shared.presentation.bot.money import money_text


def _lines(card: OrderCardView, translate: ITranslator) -> str:
    return "\n".join(
        translate(
            texts.CARD_LINE,
            title=line.title,
            article=line.article,
            variant=variant_suffix(line.variant_title, translate),
            quantity=line.quantity,
            total=money_text(line.total),
        )
        for line in card.lines
    )


def _manager(card: OrderCardView, translate: ITranslator) -> str:
    if card.manager_id is None:
        return translate(texts.CARD_UNTAKEN)
    return translate(texts.CARD_MANAGER, manager=str(card.manager_id))


def _card_text(card: OrderCardView, translate: ITranslator) -> str:
    comment = (
        ""
        if not card.comment
        else translate(texts.CARD_COMMENT, comment=card.comment)
    )
    return translate(
        texts.CARD,
        number=card.number,
        status=translate(status_key(card.status)),
        manager=_manager(card, translate),
        items=_lines(card, translate),
        total=money_text(card.total),
        name=card.name,
        phone=card.phone,
        address=card.address,
        customer=str(card.customer_id),
        comment=comment,
    )


ORDER_CARD: Screen[OrderCardView] = Screen(
    content=_card_text,
    buttons=[TAKE, PAID, SHIPPED, DONE, CANCEL],
    row_width=2,
    layout=(1,),
)
