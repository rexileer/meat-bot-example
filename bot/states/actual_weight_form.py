from aiogram.dispatcher.filters.state import StatesGroup, State


class ActualWeight(StatesGroup):
    weight = State()
