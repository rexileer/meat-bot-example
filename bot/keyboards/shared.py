from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from Web.CRM.constans.separator import SEPARATORS, SEPARATOR_MODES


def skip_keyboard(add_return: bool = True) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton(text="Пропустить"))
    if add_return:
        keyboard.add(KeyboardButton(text="Назад"))
    return keyboard


def set_status_keyboard(statuses) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        *[KeyboardButton(text=status.name) for status in statuses],
    )
    keyboard.row(KeyboardButton(text="Назад"))
    return keyboard


def set_minced_meat_batch(minced_meat_batches):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        *[
            KeyboardButton(text=f"{minced_meat_batch.production_id} ({minced_meat_batch.recipe.name})")
            for minced_meat_batch in minced_meat_batches
        ],
    )
    keyboard.row(KeyboardButton(text="Назад"))
    return keyboard


def set_separator_name_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(*[KeyboardButton(text=separator) for separator in SEPARATORS])
    keyboard.row(KeyboardButton(text="Назад"))
    return keyboard


def set_separator_mode_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(*[KeyboardButton(text=separator_mode) for separator_mode in SEPARATOR_MODES])
    keyboard.row(KeyboardButton(text="Назад"))
    return keyboard


def return_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton(text="Назад"))
    return keyboard
