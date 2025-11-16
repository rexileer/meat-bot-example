from aiogram.dispatcher.filters.state import StatesGroup, State


class NewMincedMeatBatchForm(StatesGroup):
    set_recipe = State()

    set_material_type = State()

    set_line_type = State()
    set_night = State()

    set_meat_blanks = State()
    set_second_release_minced_meat = State()
    set_raw_materials = State()

    set_raw_meat_batch = State()
    set_weight = State()
    set_weight_meat_blank = State()
    set_weight_release_minced_meat = State()
    preview = State()
    set_number_mix = State()
    set_arrival_date = State()
