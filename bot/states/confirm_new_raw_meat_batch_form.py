from aiogram.dispatcher.filters.state import StatesGroup, State


class ConfirmNewRawMeatBatchForm(StatesGroup):
    set_future_raw_meat_batch = State()
