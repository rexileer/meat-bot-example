from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from Web.CRM.models import Users
from bot.keyboards.storekeeper.storekeeper_keyboards import shocker_storekeeper_actions


def main_menu_keyboard_back(telegram_id) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)

    # if telegram_id in settings.STOREKEEPER:
    #     pass

    kbs = [
        InlineKeyboardButton(text="Новая партия", callback_data="main_menu_new_raw_meat_batch"),
        InlineKeyboardButton(text="Лаборатория", callback_data="main_menu_laboratory"),
        InlineKeyboardButton(text="Лаборатория (замесы)", callback_data="laboratory_mixes"),
        InlineKeyboardButton(text="Новый фарш", callback_data="main_menu_new_minced_meat_batch"),
        InlineKeyboardButton(text="Новая заготовка", callback_data="main_menu_new_meat_blank"),
        InlineKeyboardButton(text="Занесение вторфарша", callback_data="add_second_minced_meat"),
        InlineKeyboardButton(text="Новая заготовка Марс", callback_data="new_meat_blank_mko"),
        InlineKeyboardButton(text="Создать фарш Марс", callback_data="new_minced_meat_mko"),
    ]
    keyboard.add(*kbs)

    #  InlineKeyboardButton(text=_("buttons.main_menu_set_meat_batch_status")),
    #  print(settings.TELEGRAM_SPECIAL_USER)
    # if telegram_id == int(settings.TELEGRAM_SPECIAL_USER):
    #     keyboard.add(InlineKeyboardButton(text=_("buttons.main_menu_generate_chef_report"),
    #                                       callback_data="main_menu_generate_chef_report"))
    # if telegram_id == int(settings.TELEGRAM_DEFROST_MANAGER):
    #     keyboard.add(*[InlineKeyboardButton(text=_("buttons.enable_defrost"),
    #                                         callback_data="enable_defrost"),
    #                    InlineKeyboardButton(text=_("buttons.disable_defrost"),
    #                                         callback_data="disable_defrost")]
    #                  )

    return keyboard


def main_menu_keyboard(telegram_id) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)

    if telegram_id == Users.list_roles.technologist.telegram_id or telegram_id == 6567362342:
        keyboard.add(
            *[
                InlineKeyboardButton(text="Создать фарш Марс", callback_data="new_minced_meat_mko"),
                InlineKeyboardButton(text="Новый фарш", callback_data="main_menu_new_minced_meat_batch"),
            ]
        )
    if telegram_id == Users.list_roles.technologist.telegram_id or telegram_id == 6567362342:
        keyboard.add(
            *[
                InlineKeyboardButton(text="Новая заготовка", callback_data="main_menu_new_meat_blank"),
                InlineKeyboardButton(text="Новая заготовка Марс", callback_data="new_meat_blank_mko"),
                InlineKeyboardButton(text="Занесение вторфарша", callback_data="add_second_minced_meat"),
            ]
        )
    if telegram_id == Users.list_roles.packer.telegram_id or telegram_id == 6567362342:
        keyboard.add(*[InlineKeyboardButton(text="Ближайшая выгрузка", callback_data="next_unloading")])
    if telegram_id == Users.list_roles.raw_material_reciver.telegram_id or telegram_id == 6567362342:
        keyboard.add(*[InlineKeyboardButton(text="Новая партия", callback_data="main_menu_new_raw_meat_batch")])

    if telegram_id == Users.list_roles.labaratory.telegram_id or telegram_id == 6567362342:
        keyboard.add(
            *[
                InlineKeyboardButton(text="Лаборатория", callback_data="main_menu_laboratory"),
                InlineKeyboardButton(text="Лаборатория (замесы)", callback_data="laboratory_mixes"),
                InlineKeyboardButton(text="Лаборатория (зола)", callback_data="laboratory_pitch"),
            ],
        )
    if telegram_id == Users.list_roles.storekeeper_shocker.telegram_id or telegram_id == 6567362342:
        keyboard.add(*shocker_storekeeper_actions())
        keyboard.add(
            *[InlineKeyboardButton(text="Лаборатория", callback_data="main_menu_laboratory")],
        )
    if telegram_id == Users.list_roles.storekeeper.telegram_id or telegram_id == 6567362342:
        keyboard.add(
            *[InlineKeyboardButton(text="Принять", callback_data="unload_meat")],
        )

    return keyboard

    #  InlineKeyboardButton(text=_("buttons.main_menu_set_meat_batch_status")),
    #  print(settings.TELEGRAM_SPECIAL_USER)
    # if telegram_id == int(settings.TELEGRAM_SPECIAL_USER):
    #     keyboard.add(InlineKeyboardButton(text=_("buttons.main_menu_generate_chef_report"),
    #                                       callback_data="main_menu_generate_chef_report"))
    # if telegram_id == int(settings.TELEGRAM_DEFROST_MANAGER):
    #     keyboard.add(*[InlineKeyboardButton(text=_("buttons.enable_defrost"),
    #                                         callback_data="enable_defrost"),
    #                    InlineKeyboardButton(text=_("buttons.disable_defrost"),
    #                                         callback_data="disable_defrost")]
    #                  )
