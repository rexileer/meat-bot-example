from aiogram.dispatcher.filters.state import StatesGroup, State


class DefrostWeight(StatesGroup):
    weight = State()
