from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from Web.CRM.constans.responsible import RESPONSIBLE


def set_responsible_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for responsible in RESPONSIBLE:
        keyboard.add(KeyboardButton(text=responsible))

    keyboard.row(KeyboardButton(text="Назад"))
    return keyboard


def set_organoleptic_photos_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    keyboard.add(KeyboardButton(text="Продолжить"), KeyboardButton(text="Назад"))
    return keyboard


def laboratory_compiles_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    keyboard.add(
        KeyboardButton(text="Соответствует"), KeyboardButton(text="Не соответствует"), KeyboardButton(text="Назад")
    )
    return keyboard


def laboratory_antibiotic_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    keyboard.add(
        KeyboardButton(text="Положительное"), KeyboardButton(text="Отрицательное"), KeyboardButton(text="Назад")
    )
    return keyboard


def laboratory_set_broth_quality_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    keyboard.add(
        KeyboardButton(text="Мутный"),
        KeyboardButton(text="Светлый"),
        KeyboardButton(text="Полупрозрачный"),
        KeyboardButton(text="Назад"),
    )
    return keyboard


def laboratory_confirm_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    keyboard.add(
        KeyboardButton(text="Подтвердить"),
        KeyboardButton(text="Отправить измененный"),
    )
    return keyboard
