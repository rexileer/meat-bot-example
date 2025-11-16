from aiogram.dispatcher.filters.state import StatesGroup, State


class FHPAnalysis(StatesGroup):
    set_fats = State()
    set_proteins = State()
    set_moisture = State()
    set_pitch = State()
