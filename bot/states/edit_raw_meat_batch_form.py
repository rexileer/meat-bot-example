from aiogram.dispatcher.filters.state import StatesGroup, State


class EditRawMeatBatchForm(StatesGroup):
    set_photo_ypd = State()
    set_photo_ttn = State()
    set_photo_tn = State()
    set_photo_vet = State()
    set_photo_temperature = State()
    set_photo_pallet = State()
