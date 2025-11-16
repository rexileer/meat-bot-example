from aiogram.dispatcher.filters.state import StatesGroup, State


class ChefReportForm(StatesGroup):
    choice = State()
    send_new_table = State()
