from aiogram.dispatcher.filters.state import StatesGroup, State


class FutureRawMeatBatchForm(StatesGroup):
    set_weight = State()
    set_raw_material = State()
