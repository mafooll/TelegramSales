from aiogram import Router

from telegramsales.modules.catalog.presentation.bot.routers import (
    browse,
    edit,
    product_form,
    products,
    shop,
    titles,
)
from telegramsales.shared.presentation.bot.errors import report_domain_errors
from telegramsales.shared.presentation.bot.filters import HasActorFilter

catalog_router = Router(name="catalog")
catalog_router.message.filter(HasActorFilter())
catalog_router.callback_query.filter(HasActorFilter())

catalog_router.include_router(shop.router)
catalog_router.include_router(browse.router)
catalog_router.include_router(edit.router)
catalog_router.include_router(products.router)
catalog_router.include_router(product_form.router)
catalog_router.include_router(titles.router)

report_domain_errors(catalog_router)

__all__ = ["catalog_router"]
