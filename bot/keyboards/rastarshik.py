from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def rastarshchik_action(blank_id):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(*[InlineKeyboardButton("Заготовка растарена", callback_data=f"accpet_rastareno-{blank_id}")])
    kb.add(*[InlineKeyboardButton("Ошибка", callback_data=f"declime_rastareno-{blank_id}")])
    return kb


def rastarshik_minced_meat_keyboard(mix_id) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(*[InlineKeyboardButton(text="Замес растарен", callback_data=f"a_minc_mix-{mix_id}")])
    keyboard.add(*[InlineKeyboardButton(text="Помощь", callback_data="storekeeper_help")])
    return keyboard
