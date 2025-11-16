from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from Web.CRM.models import BufferPalletMars


def start_blank_actual_weight(blank_id):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(*[InlineKeyboardButton("Ввести фактический вес сырья", callback_data=f"start_actual_weight-{blank_id}")])
    return kb


def shocker_storekeeper_actions():
    return [
        InlineKeyboardButton("Заморозка фарша Марс", callback_data="mars_shock"),
        InlineKeyboardButton("Заморозка МКО2", callback_data="add_second_minced_meat_mko_2"),
        InlineKeyboardButton("Заморозка МКО3", callback_data="add_second_minced_meat_mko_3"),
    ]


def storekeeper_mars_remains_actions():
    kb = InlineKeyboardMarkup(row_width=1)
    check_pallets = BufferPalletMars.objects.filter(box_count__lt=45).count()
    if check_pallets:
        kb.add(
            *[
                InlineKeyboardButton("Добавить в буферный паллет остатки", callback_data="add_to_buffer_pallet"),
            ]
        )
    else:
        kb.add(
            *[
                InlineKeyboardButton("Создать буферный паллет", callback_data="create_buffer_pallet"),
            ]
        )
    kb.add(
        *[
            InlineKeyboardButton("Назад", callback_data="mars_shock"),
        ]
    )
    return kb


def storekeeper_mars_actions():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        *[
            InlineKeyboardButton("Заморозить фарш марс", callback_data="mars_to_shocker"),
            InlineKeyboardButton("Заморозка остатков", callback_data="remains_mars"),
            InlineKeyboardButton("Назад", callback_data="return"),
        ]
    )
    return kb
