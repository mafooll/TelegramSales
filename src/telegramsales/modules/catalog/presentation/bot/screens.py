from telegramsales.modules.catalog.application.queries import (
    BrandView,
    CatalogView,
    CategoryView,
)
from telegramsales.modules.catalog.presentation.bot import texts
from telegramsales.modules.catalog.presentation.bot.buttons import (
    BACK_TO_CATALOG,
    BACK_TO_PARENT,
    BRAND_ENTRY,
    CATALOG_ENTRY,
    CATEGORY_ENTRY,
    CREATE_BRAND,
    CREATE_CATALOG,
    CREATE_CATEGORY,
    CREATE_SUBCATEGORY,
    DELETE_BRAND,
    DELETE_CATALOG,
    DELETE_CATEGORY,
    HIDE_BRAND,
    HIDE_CATALOG,
    HIDE_CATEGORY,
    OPEN_BRANDS,
    OPEN_CATALOGS,
    RENAME_BRAND,
    RENAME_CATALOG,
    RENAME_CATEGORY,
    SHOW_BRAND,
    SHOW_CATALOG,
    SHOW_CATEGORY,
    back_to_brands,
    back_to_catalogs,
    back_to_hub,
)
from telegramsales.modules.catalog.presentation.bot.views import CountedView
from telegramsales.shared.presentation.bot.keyboard import ListScreen, Screen, label
from telegramsales.shared.presentation.bot.navigation import home_button

HUB: Screen[None] = Screen(
    content=label(texts.HUB),
    buttons=[OPEN_CATALOGS, OPEN_BRANDS, home_button()],
)

CATALOG_LIST: ListScreen[CatalogView, CountedView] = ListScreen(
    content=lambda view, translate: translate(
        texts.CATALOG_LIST_EMPTY if view.total == 0 else texts.CATALOG_LIST,
        total=view.total,
    ),
    item=CATALOG_ENTRY,
    footer=[CREATE_CATALOG, back_to_hub()],
)

CATALOG_CARD: ListScreen[CategoryView, CatalogView] = ListScreen(
    content=lambda catalog, translate: translate(
        texts.CATALOG_CARD,
        title=catalog.title,
        count=catalog.category_count,
    ),
    item=CATEGORY_ENTRY,
    footer=[
        CREATE_CATEGORY,
        RENAME_CATALOG,
        HIDE_CATALOG,
        SHOW_CATALOG,
        DELETE_CATALOG,
        back_to_catalogs(),
    ],
)

CATEGORY_CARD: ListScreen[CategoryView, CategoryView] = ListScreen(
    content=lambda category, translate: translate(
        texts.CATEGORY_CARD,
        title=category.title,
        count=category.child_count,
    ),
    item=CATEGORY_ENTRY,
    footer=[
        CREATE_SUBCATEGORY,
        RENAME_CATEGORY,
        HIDE_CATEGORY,
        SHOW_CATEGORY,
        DELETE_CATEGORY,
        BACK_TO_CATALOG,
        BACK_TO_PARENT,
    ],
)

BRAND_LIST: ListScreen[BrandView, CountedView] = ListScreen(
    content=lambda view, translate: translate(
        texts.BRAND_LIST_EMPTY if view.total == 0 else texts.BRAND_LIST,
        total=view.total,
    ),
    item=BRAND_ENTRY,
    footer=[CREATE_BRAND, back_to_hub()],
)

BRAND_CARD: Screen[BrandView] = Screen(
    content=lambda brand, translate: translate(texts.BRAND_CARD, title=brand.title),
    buttons=[
        RENAME_BRAND,
        HIDE_BRAND,
        SHOW_BRAND,
        DELETE_BRAND,
        back_to_brands(),
    ],
)
