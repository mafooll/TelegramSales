from aiogram.enums import ButtonStyle

from telegramsales.modules.catalog.application.queries import (
    BrandView,
    CatalogView,
    CategoryView,
)
from telegramsales.modules.catalog.domain.permissions import CatalogPermission
from telegramsales.modules.catalog.presentation.bot import texts
from telegramsales.modules.catalog.presentation.bot.callbacks import (
    CatalogAction,
    CatalogCallback,
    CatalogTarget,
)
from telegramsales.modules.catalog.presentation.bot.views import (
    CountedView,
    PromptView,
    brand_item_key,
    catalog_item_key,
    category_item_key,
)
from telegramsales.shared.presentation.bot.keyboard import Button, label

CANCEL_INPUT: Button[PromptView] = Button(
    text=label(texts.CANCEL_BUTTON),
    callback=lambda view: view.back,
)

OPEN_CATALOGS: Button[None] = Button(
    text=label(texts.HUB_CATALOGS_BUTTON),
    callback=lambda _: CatalogCallback(
        action=CatalogAction.LIST,
        target=CatalogTarget.CATALOG,
    ),
)

OPEN_BRANDS: Button[None] = Button(
    text=label(texts.HUB_BRANDS_BUTTON),
    callback=lambda _: CatalogCallback(
        action=CatalogAction.LIST,
        target=CatalogTarget.BRAND,
    ),
)


def back_to_hub[ViewType]() -> Button[ViewType]:
    return Button(
        text=label(texts.BACK_BUTTON),
        callback=lambda _: CatalogCallback(action=CatalogAction.HUB),
    )


CATALOG_ENTRY: Button[CatalogView] = Button(
    text=lambda catalog, translate: translate(
        catalog_item_key(catalog),
        title=catalog.title,
        count=catalog.category_count,
    ),
    callback=lambda catalog: CatalogCallback(
        action=CatalogAction.CARD,
        target=CatalogTarget.CATALOG,
        catalog_id=catalog.id,
    ),
)

CREATE_CATALOG: Button[CountedView] = Button(
    text=label(texts.CATALOG_CREATE_BUTTON),
    callback=lambda _: CatalogCallback(
        action=CatalogAction.ASK_CREATE,
        target=CatalogTarget.CATALOG,
    ),
    permission=CatalogPermission.MANAGE,
    style=ButtonStyle.PRIMARY,
)

CATEGORY_ENTRY: Button[CategoryView] = Button(
    text=lambda category, translate: translate(
        category_item_key(category),
        title=category.title,
        count=category.child_count,
    ),
    callback=lambda category: CatalogCallback(
        action=CatalogAction.CARD,
        target=CatalogTarget.CATEGORY,
        catalog_id=category.catalog_id,
        category_id=category.id,
    ),
)

CREATE_CATEGORY: Button[CatalogView] = Button(
    text=label(texts.CATEGORY_CREATE_BUTTON),
    callback=lambda catalog: CatalogCallback(
        action=CatalogAction.ASK_CREATE,
        target=CatalogTarget.CATEGORY,
        catalog_id=catalog.id,
    ),
    permission=CatalogPermission.MANAGE,
    style=ButtonStyle.PRIMARY,
)

CREATE_SUBCATEGORY: Button[CategoryView] = Button(
    text=label(texts.SUBCATEGORY_CREATE_BUTTON),
    callback=lambda category: CatalogCallback(
        action=CatalogAction.ASK_CREATE,
        target=CatalogTarget.CATEGORY,
        catalog_id=category.catalog_id,
        category_id=category.id,
    ),
    permission=CatalogPermission.MANAGE,
    when=lambda category: category.parent_id is None,
    style=ButtonStyle.PRIMARY,
)

BRAND_ENTRY: Button[BrandView] = Button(
    text=lambda brand, translate: translate(
        brand_item_key(brand), title=brand.title
    ),
    callback=lambda brand: CatalogCallback(
        action=CatalogAction.CARD,
        target=CatalogTarget.BRAND,
        brand_id=brand.id,
    ),
)

CREATE_BRAND: Button[CountedView] = Button(
    text=label(texts.BRAND_CREATE_BUTTON),
    callback=lambda _: CatalogCallback(
        action=CatalogAction.ASK_CREATE,
        target=CatalogTarget.BRAND,
    ),
    permission=CatalogPermission.MANAGE,
    style=ButtonStyle.PRIMARY,
)

RENAME_CATALOG: Button[CatalogView] = Button(
    text=label(texts.RENAME_BUTTON),
    callback=lambda catalog: CatalogCallback(
        action=CatalogAction.ASK_RENAME,
        target=CatalogTarget.CATALOG,
        catalog_id=catalog.id,
    ),
    permission=CatalogPermission.MANAGE,
)

HIDE_CATALOG: Button[CatalogView] = Button(
    text=label(texts.HIDE_BUTTON),
    callback=lambda catalog: CatalogCallback(
        action=CatalogAction.HIDE,
        target=CatalogTarget.CATALOG,
        catalog_id=catalog.id,
    ),
    permission=CatalogPermission.MANAGE,
    when=lambda catalog: catalog.is_active,
)

SHOW_CATALOG: Button[CatalogView] = Button(
    text=label(texts.SHOW_BUTTON),
    callback=lambda catalog: CatalogCallback(
        action=CatalogAction.SHOW,
        target=CatalogTarget.CATALOG,
        catalog_id=catalog.id,
    ),
    permission=CatalogPermission.MANAGE,
    when=lambda catalog: not catalog.is_active,
    style=ButtonStyle.SUCCESS,
)

DELETE_CATALOG: Button[CatalogView] = Button(
    text=label(texts.DELETE_BUTTON),
    callback=lambda catalog: CatalogCallback(
        action=CatalogAction.ASK_DELETE,
        target=CatalogTarget.CATALOG,
        catalog_id=catalog.id,
    ),
    permission=CatalogPermission.MANAGE,
    when=lambda catalog: catalog.category_count == 0,
    style=ButtonStyle.DANGER,
)


def back_to_catalogs[ViewType]() -> Button[ViewType]:
    return Button(
        text=label(texts.BACK_BUTTON),
        callback=lambda _: CatalogCallback(
            action=CatalogAction.LIST,
            target=CatalogTarget.CATALOG,
        ),
    )


RENAME_CATEGORY: Button[CategoryView] = Button(
    text=label(texts.RENAME_BUTTON),
    callback=lambda category: CatalogCallback(
        action=CatalogAction.ASK_RENAME,
        target=CatalogTarget.CATEGORY,
        category_id=category.id,
    ),
    permission=CatalogPermission.MANAGE,
)

HIDE_CATEGORY: Button[CategoryView] = Button(
    text=label(texts.HIDE_BUTTON),
    callback=lambda category: CatalogCallback(
        action=CatalogAction.HIDE,
        target=CatalogTarget.CATEGORY,
        category_id=category.id,
    ),
    permission=CatalogPermission.MANAGE,
    when=lambda category: category.is_active,
)

SHOW_CATEGORY: Button[CategoryView] = Button(
    text=label(texts.SHOW_BUTTON),
    callback=lambda category: CatalogCallback(
        action=CatalogAction.SHOW,
        target=CatalogTarget.CATEGORY,
        category_id=category.id,
    ),
    permission=CatalogPermission.MANAGE,
    when=lambda category: not category.is_active,
    style=ButtonStyle.SUCCESS,
)

DELETE_CATEGORY: Button[CategoryView] = Button(
    text=label(texts.DELETE_BUTTON),
    callback=lambda category: CatalogCallback(
        action=CatalogAction.ASK_DELETE,
        target=CatalogTarget.CATEGORY,
        category_id=category.id,
    ),
    permission=CatalogPermission.MANAGE,
    when=lambda category: category.child_count == 0,
    style=ButtonStyle.DANGER,
)

BACK_TO_CATALOG: Button[CategoryView] = Button(
    text=label(texts.BACK_BUTTON),
    callback=lambda category: CatalogCallback(
        action=CatalogAction.CARD,
        target=CatalogTarget.CATALOG,
        catalog_id=category.catalog_id,
    ),
    when=lambda category: category.parent_id is None,
)

BACK_TO_PARENT: Button[CategoryView] = Button(
    text=label(texts.BACK_BUTTON),
    callback=lambda category: CatalogCallback(
        action=CatalogAction.CARD,
        target=CatalogTarget.CATEGORY,
        catalog_id=category.catalog_id,
        category_id=category.parent_id,
    ),
    when=lambda category: category.parent_id is not None,
)

RENAME_BRAND: Button[BrandView] = Button(
    text=label(texts.RENAME_BUTTON),
    callback=lambda brand: CatalogCallback(
        action=CatalogAction.ASK_RENAME,
        target=CatalogTarget.BRAND,
        brand_id=brand.id,
    ),
    permission=CatalogPermission.MANAGE,
)

HIDE_BRAND: Button[BrandView] = Button(
    text=label(texts.HIDE_BUTTON),
    callback=lambda brand: CatalogCallback(
        action=CatalogAction.HIDE,
        target=CatalogTarget.BRAND,
        brand_id=brand.id,
    ),
    permission=CatalogPermission.MANAGE,
    when=lambda brand: brand.is_active,
)

SHOW_BRAND: Button[BrandView] = Button(
    text=label(texts.SHOW_BUTTON),
    callback=lambda brand: CatalogCallback(
        action=CatalogAction.SHOW,
        target=CatalogTarget.BRAND,
        brand_id=brand.id,
    ),
    permission=CatalogPermission.MANAGE,
    when=lambda brand: not brand.is_active,
    style=ButtonStyle.SUCCESS,
)

DELETE_BRAND: Button[BrandView] = Button(
    text=label(texts.DELETE_BUTTON),
    callback=lambda brand: CatalogCallback(
        action=CatalogAction.ASK_DELETE,
        target=CatalogTarget.BRAND,
        brand_id=brand.id,
    ),
    permission=CatalogPermission.MANAGE,
    style=ButtonStyle.DANGER,
)


def back_to_brands[ViewType]() -> Button[ViewType]:
    return Button(
        text=label(texts.BACK_BUTTON),
        callback=lambda _: CatalogCallback(
            action=CatalogAction.LIST,
            target=CatalogTarget.BRAND,
        ),
    )
