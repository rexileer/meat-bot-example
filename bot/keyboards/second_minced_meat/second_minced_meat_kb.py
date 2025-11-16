from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from Web.CRM.models import ShockerCamera


def add_second_minced_kb() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        *[
            InlineKeyboardButton(text="Добавить МКО1", callback_data="add_second_minced_meat_mko_1"),
            InlineKeyboardButton(text="Выпуск вторфарша", callback_data="release_second_minced_meat"),
            InlineKeyboardButton(text="Главное меню", callback_data="return"),
        ]
    )
    return keyboard


def select_shocker() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=4)
    shocker_list = sorted([key for key, val in ShockerCamera.get_available_shocker().items() if val > 0])
    keyboard.add(
        *[
            InlineKeyboardButton(
                text=f"{i}", callback_data=f"select_shocker-{ShockerCamera.objects.get(shocker_id=i).pk}"
            )
            for i in shocker_list
        ]
    )

    if not len(shocker_list):
        keyboard.add(InlineKeyboardButton(text="Обновить", callback_data="refresh_shockers"))
    keyboard.add(InlineKeyboardButton(text="Главное меню", callback_data="return"))

    return keyboard


def cheburashka_select_and_back() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        *[
            InlineKeyboardButton(text="Чебурашка №1 (27 кг)", callback_data="cheburashka_1"),
            InlineKeyboardButton(text="Чебурашка №2 (43 кг)", callback_data="cheburashka_2"),
            InlineKeyboardButton(text="Главное меню", callback_data="return"),
        ]
    )
    return keyboard


def back_to_main_menu() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(*[InlineKeyboardButton(text="Главное меню", callback_data="return")])
    return keyboard
