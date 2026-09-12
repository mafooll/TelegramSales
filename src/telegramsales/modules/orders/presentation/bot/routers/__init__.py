from aiogram import Router

from telegramsales.modules.orders.presentation.bot.routers import (
    cart,
    checkout,
    orders,
    selections,
)
from telegramsales.shared.presentation.bot.errors import report_domain_errors
from telegramsales.shared.presentation.bot.filters import HasActorFilter

orders_router = Router(name="orders")
orders_router.message.filter(HasActorFilter())
orders_router.callback_query.filter(HasActorFilter())

orders_router.include_router(selections.router)
orders_router.include_router(cart.router)
orders_router.include_router(checkout.router)
orders_router.include_router(orders.router)

report_domain_errors(orders_router)

__all__ = ["orders_router"]
