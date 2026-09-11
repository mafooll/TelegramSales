from typing import final

from aiogram.fsm.state import State, StatesGroup


@final
class ProductForm(StatesGroup):
    title = State()
    description = State()
    price = State()
    photos = State()
    rename = State()
    redescribe = State()
    reprice = State()
    axis = State()
    variant = State()
