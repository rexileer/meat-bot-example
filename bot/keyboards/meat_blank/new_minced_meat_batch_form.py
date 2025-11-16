from typing import List

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from Web.CRM.models import Recipe, RawMeatBatch, MeatBlank


def set_recipe_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    recipes = Recipe.objects.all()
    keyboard.add(*[KeyboardButton(text=recipe.name) for recipe in recipes])
    keyboard.row(KeyboardButton("Назад"))
    return keyboard


def set_return_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(KeyboardButton("Назад"))
    return keyboard


def set_raw_materials_keyboard(meat_batches: List[RawMeatBatch]) -> ReplyKeyboardMarkup:
    raw_materials = []
    for meat_batch in meat_batches:
        if meat_batch.raw_material.name not in raw_materials:
            raw_materials.append(meat_batch.raw_material.name)

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    keyboard.add(*[KeyboardButton(text=raw_material) for raw_material in raw_materials])
    keyboard.row(KeyboardButton("Вернуться"))
    return keyboard


def set_material_type_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton(text="Заготовка"), KeyboardButton(text="Сырье"))
    keyboard.row(KeyboardButton("Назад"))
    return keyboard


def set_material_type_keyboard_mko() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton(text="Заготовка"), KeyboardButton(text="Вторфарш"))
    keyboard.row(KeyboardButton("Назад"))
    return keyboard


def set_second_minced_meat_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.row(KeyboardButton("Использовать все"))
    keyboard.row(KeyboardButton("Назад"))
    return keyboard


def set_meat_blank_keyboard(meat_blanks: List[MeatBlank]) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for meat_blank in meat_blanks:
        keyboard.add(KeyboardButton(text=meat_blank.production_id))
    keyboard.row(KeyboardButton("Вернуться"))
    return keyboard


def set_raw_meat_batch_keyboard(raw_meat_batches: List[RawMeatBatch]) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for raw_meat_batch in raw_meat_batches:
        keyboard.add(KeyboardButton(text=raw_meat_batch.production_id))
    keyboard.row(KeyboardButton("Вернуться"))
    return keyboard


def set_weight_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton(text="Все"))
    keyboard.row(KeyboardButton("Вернуться"))
    return keyboard


def set_arrival_date_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    keyboard.add(KeyboardButton(text="Сегодня"), KeyboardButton(text="Завтра"))
    keyboard.row(KeyboardButton("Назад"))
    return keyboard


def set_line_minced_meat_keyboard(state_data) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)
    is_mko = state_data.get("is_mko")
    if not is_mko:
        keyboard.add(
            *[
                InlineKeyboardButton(text="Линия 1", callback_data="minced_meat_batch_line-1"),
                InlineKeyboardButton(text="Линия 2", callback_data="minced_meat_batch_line-2"),
            ]
        )
        keyboard.add(*[InlineKeyboardButton(text="Обе", callback_data="minced_meat_batch_line-10")])
    else:
        keyboard.add(
            *[InlineKeyboardButton(text="Линия марса 1 (плиточник)", callback_data="minced_meat_batch_line-1")],
            *[InlineKeyboardButton(text="Линия марса 2 (шокер)", callback_data="minced_meat_batch_line-2")]
        )
    keyboard.add(*[InlineKeyboardButton(text="Назад", callback_data="return")])
    return keyboard


def set_nigth_minced_meat_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(*[InlineKeyboardButton(text="Текущая смена", callback_data="minced_meat_batch_night-False")])
    keyboard.add(*[InlineKeyboardButton(text="Ночь", callback_data="minced_meat_batch_night-True")])

    keyboard.add(*[InlineKeyboardButton(text="Назад", callback_data="return")])
    return keyboard
