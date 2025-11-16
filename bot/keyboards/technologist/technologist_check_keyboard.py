from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def set_technologist_check_keyboard(user_id, stage, value) -> InlineKeyboardMarkup:
    uptate_table_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"tech_check_app:{user_id}:{stage}:{value}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"tech_check_can:{user_id}:{stage}:{value}"),
            ]
        ]
    )

    return uptate_table_keyboard


def accept_work_line_status(mix_id) -> InlineKeyboardMarkup:
    uptate_table_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да", callback_data=f"tech_line:yes:{mix_id}"),
                InlineKeyboardButton(text="❌ Нет", callback_data=f"tech_line:no:{mix_id}"),
            ]
        ]
    )

    return uptate_table_keyboard


def set_continue_keyboard(stage, value) -> InlineKeyboardMarkup:
    uptate_table_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Продолжить", callback_data=f"check_continue:{stage}:{value}"),
            ]
        ]
    )

    return uptate_table_keyboard


def next_from_photo_storekeepers() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(*[InlineKeyboardButton(text="Продолжить", callback_data="sto_mar_continue_photo")])
    return keyboard


def finish_storekeepers_minced_meat() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(*[InlineKeyboardButton(text="Принять", callback_data="sto_mar_finish")])
    keyboard.add(*[InlineKeyboardButton(text="Начать заново", callback_data="sto_mar_reset")])
    return keyboard
