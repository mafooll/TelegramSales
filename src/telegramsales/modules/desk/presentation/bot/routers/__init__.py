from aiogram import Router

from telegramsales.modules.desk.presentation.bot.routers import cards, relay
from telegramsales.shared.presentation.bot.errors import report_domain_errors
from telegramsales.shared.presentation.bot.filters import HasActorFilter

desk_router = Router(name="desk")
desk_router.callback_query.filter(HasActorFilter())

desk_router.include_router(cards.router)
desk_router.include_router(relay.router)

report_domain_errors(desk_router)

__all__ = ["desk_router"]
