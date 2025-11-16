from aiogram.dispatcher.filters.state import StatesGroup, State


class SecondMincedMeatMKO_1(StatesGroup):
    set_weight = State()
    set_weight_cart = State()


class SecondMincedMeatMKO_Release(StatesGroup):
    set_weight = State()
    set_weight_cart = State()


class SecondMincedMeatMKO_2_3(StatesGroup):
    set_mko_3_weight = State()
    set_pallet_num = State()
    set_pallet_weight = State()
    set_box_count = State()
    set_brutto_weight = State()
    set_shock_chamber_num = State()
