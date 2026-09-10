from aiogram import Router

from telegramsales.modules.staff.presentation.bot.routers import (
    access,
    browse,
    roles,
)
from telegramsales.shared.presentation.bot.errors import report_domain_errors
from telegramsales.shared.presentation.bot.filters import HasActorFilter

staff_router = Router(name="staff")
staff_router.message.filter(HasActorFilter())
staff_router.callback_query.filter(HasActorFilter())

staff_router.include_router(browse.router)
staff_router.include_router(access.router)
staff_router.include_router(roles.router)

report_domain_errors(staff_router)

__all__ = ["staff_router"]
