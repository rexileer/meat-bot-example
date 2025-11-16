from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from Web.CRM.models import Company


def raw_material_keyboard(raw_materials) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        *[KeyboardButton(text=raw_material.name) for raw_material in raw_materials],
    )
    keyboard.row(KeyboardButton(text="Назад"))
    return keyboard


def set_companies_keyboard() -> ReplyKeyboardMarkup:
    companies_obj = Company.objects.all()
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        *[KeyboardButton(text=company.name) for company in companies_obj],
    )
    keyboard.row(KeyboardButton(text="Назад"))
    return keyboard


def set_weight_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    keyboard.add(
        KeyboardButton(text="Совпадает"),
        KeyboardButton(text="Не совпадает"),
        KeyboardButton(text="Назад"),
    )
    return keyboard


def set_photo_vet_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    keyboard.add(
        KeyboardButton(text="Подтвердить"),
        KeyboardButton(text="Назад"),
    )
    return keyboard


def set_condition_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    keyboard.add(
        KeyboardButton(text="Охлажденное"),
        KeyboardButton(text="Замороженое"),
        KeyboardButton(text="Назад"),
    )
    return keyboard


def set_photo_ttn_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    keyboard.add(KeyboardButton(text="Подтвердить"), KeyboardButton(text="Назад"))
    return keyboard


def set_buh_accounting_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    keyboard.add(
        KeyboardButton(text="Суп"),
        KeyboardButton(text="Киль"),
        KeyboardButton(text="Каркас"),
        KeyboardButton(text="Трубч.кость"),
    )
    return keyboard
