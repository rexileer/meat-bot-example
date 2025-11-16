from aiogram.dispatcher.filters.state import StatesGroup, State


class LaboratoryForm(StatesGroup):
    set_meat_batch_id = State()


class LaboratoryAnalyzeForm(StatesGroup):
    set_fat_proportion = State()
    set_protein_proportion = State()
    set_moisture_proportion = State()
    set_appearance = State()
    set_smell = State()
    set_color = State()
    set_broth_quality = State()
    set_broth_flavor = State()
    set_betta_lactams = State()
    set_chloramphenicols = State()
    set_tetracyclines = State()
    set_streptomycins = State()
    set_organoleptic_photos = State()
    set_ttn_date = State()
    set_responsible = State()
    set_separator_name = State()
    set_separator_mode = State()
    set_temperature = State()
    confirm = State()
    set_acceptance_certificate = State()
