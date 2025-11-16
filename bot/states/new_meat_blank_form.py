from aiogram.dispatcher.filters.state import StatesGroup, State


class NewMeatBlankForm(StatesGroup):
    set_raw_materials = State()
    set_raw_meat_batch = State()
    set_weight = State()
    preview = State()
    set_arrival_date = State()
