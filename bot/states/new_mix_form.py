from aiogram.dispatcher.filters.state import StatesGroup, State


class NewMixForm(StatesGroup):
    set_minced_meat_batch = State()
    confirm_create_new_mix = State()
