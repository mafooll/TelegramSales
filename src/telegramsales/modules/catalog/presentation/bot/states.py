from typing import final

from aiogram.fsm.state import State, StatesGroup


@final
class TitleForm(StatesGroup):
    catalog = State()
    catalog_rename = State()
    category = State()
    category_rename = State()
    brand = State()
    brand_rename = State()
