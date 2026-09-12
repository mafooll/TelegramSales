from aiogram import F, Router
from aiogram.types import CallbackQuery
from dishka.integrations.aiogram import FromDishka

from telegramsales.modules.catalog.contracts import ProductId, VariantId
from telegramsales.modules.catalog.presentation.bot.shop_callbacks import (
    ShopAction,
    ShopCallback,
)
from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.orders.application.commands.cart import (
    AddToCart,
    AddToCartHandler,
)
from telegramsales.modules.orders.application.readers import CartReader
from telegramsales.modules.orders.presentation.bot import render, texts
from telegramsales.shared.presentation.bot.context import RenderContext
from telegramsales.shared.presentation.bot.errors import report_domain_errors
from telegramsales.shared.presentation.bot.filters import HasActorFilter
from telegramsales.shared.presentation.bot.render import show

router = Router(name="bot.cart")
router.callback_query.filter(HasActorFilter())


@router.callback_query(ShopCallback.filter(F.action == ShopAction.ADD))
async def add_to_cart(
    callback: CallbackQuery,
    callback_data: ShopCallback,
    context: RenderContext,
    handler: FromDishka[AddToCartHandler],
) -> None:
    if callback_data.product_id is None:
        await callback.answer()
        return

    await handler.handle(
        AddToCart(
            customer_id=CustomerId(context.actor.id),
            product_id=ProductId(callback_data.product_id),
            variant_id=(
                None
                if callback_data.variant_id is None
                else VariantId(callback_data.variant_id)
            ),
        )
    )
    await callback.answer(context.translate(texts.ADDED_TO_CART))


@router.callback_query(ShopCallback.filter(F.action == ShopAction.CART))
async def open_cart(
    callback: CallbackQuery,
    context: RenderContext,
    reader: FromDishka[CartReader],
) -> None:
    await callback.answer()
    await show(
        callback,
        await render.cart_of(reader, context, CustomerId(context.actor.id)),
    )


report_domain_errors(router)
