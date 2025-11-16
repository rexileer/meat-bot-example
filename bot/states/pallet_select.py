from aiogram.dispatcher.filters.state import StatesGroup, State


class PalletSelect(StatesGroup):
    set_to_pallet = State()
