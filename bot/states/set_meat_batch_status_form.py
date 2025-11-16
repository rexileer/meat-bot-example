from aiogram.dispatcher.filters.state import StatesGroup, State


class SetMeatBatchStatusForm(StatesGroup):
    set_meat_batch_id = State()
    # set_material = State()
    set_weight_after_defrosting = State()
    set_weight_after_unloading_kt2 = State()
    set_status = State()
    set_separator_name = State()
    set_separator_mode = State()
    pallet_weighing_set_pallet_number = State()
    pallet_weighing_set_pallet_weight = State()
    pallet_weighing_set_confirm = State()

    set_pallet_number = State()
    set_pallet_netto = State()
    set_pallet_brutto = State()
    set_pallet_pallet_weight = State()
    set_pallet_package_weight = State()
    set_pallet_shock_frost = State()
    set_pallet_temperature = State()

    set_pallet_weight = State()
    set_customer = State()

    get_time = State()
    get_place = State()
