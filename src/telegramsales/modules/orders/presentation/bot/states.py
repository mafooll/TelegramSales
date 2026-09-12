from typing import final

from aiogram.fsm.state import State, StatesGroup


@final
class Checkout(StatesGroup):
    name = State()
    phone = State()
    address = State()
    comment = State()
