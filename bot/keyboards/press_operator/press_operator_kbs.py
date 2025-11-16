from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def press_operator_minced_meat_keyboard(minced_mix_id) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(*[InlineKeyboardButton(text="Просепарировано", callback_data=f"a_press_mix-{minced_mix_id}")])
    keyboard.add(*[InlineKeyboardButton(text="Помощь", callback_data="separated_help")])
    return keyboard
